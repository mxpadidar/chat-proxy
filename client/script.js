const wsClientOne = new WebSocket("ws://localhost:8081");
const wsClientTwo = new WebSocket("ws://localhost:8082");
const clientOneStatus = document.getElementById("client-one-status");
const clientTwoStatus = document.getElementById("client-two-status");
const clientOneChat = document.getElementById("client-one-chats");
const clientTwoChat = document.getElementById("client-two-chats");

const MessageType = {
  USER_REGISTER: "user_register",
  CHAT: "chat",
  SERVER_RESPONSE: "server_response",
  SERVER_ERROR: "server_error",
};

const appendChat = (chats, message) => {
  const li = document.createElement("li");
  li.innerText = message;
  chats.appendChild(li);
};

wsClientOne.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message);

  if (message.type === MessageType.SERVER_ERROR) {
    clientOneStatus.innerText = message.body.message;
  }
  if (message.type === MessageType.SERVER_RESPONSE) {
    clientOneStatus.innerText = message.body.message;
  }
  if (message.type === MessageType.CHAT) {
    appendChat(clientOneChat, `${message.body.user}: ${message.body.message}`);
  }
};

wsClientTwo.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message);

  if (message.type === MessageType.SERVER_ERROR) {
    clientTwoStatus.innerText = message.body.message;
  }
  if (message.type === MessageType.SERVER_RESPONSE) {
    clientTwoStatus.innerText = message.body.message;
  }
  if (message.type === MessageType.CHAT) {
    appendChat(clientTwoChat, `${message.body.user}: ${message.body.message}`);
  }
};

wsClientOne.onopen = () => {
  clientOneStatus.innerText = "Connected";
  register(wsClientOne, "client1");
};

wsClientOne.onclose = () => {
  clientOneStatus.innerText = "Disconnected";
};

wsClientTwo.onopen = () => {
  clientTwoStatus.innerText = "Connected";
  register(wsClientTwo, "client2");
};

wsClientTwo.onclose = () => {
  clientTwoStatus.innerText = "Disconnected";
};

const register = (ws, username) => {
  const registerMessage = JSON.stringify({
    type: MessageType.USER_REGISTER,
    body: { user: username },
  });
  ws.send(registerMessage);
};

const sendChat = (ws, sender, recipient, message) => {
  const chatMessage = JSON.stringify({
    type: MessageType.CHAT,
    body: { user: sender, recipient, message },
  });
  ws.send(chatMessage);
};

document.getElementById("send-client-one").addEventListener("click", () => {
  const message = document.getElementById("client-one-input").value;
  sendChat(wsClientOne, "client1", "client2", message);
});

document.getElementById("send-client-two").addEventListener("click", () => {
  const message = document.getElementById("client-two-input").value;
  sendChat(wsClientTwo, "client2", "client1", message);
});
