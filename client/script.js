const wsClientOne = new WebSocket("ws://localhost:8081");
const wsClientTwo = new WebSocket("ws://localhost:8082");
const clientOneStatus = document.getElementById("client-one-status");
const clientTwoStatus = document.getElementById("client-two-status");
const clientOneChat = document.getElementById("client-one-chats");
const clientTwoChat = document.getElementById("client-two-chats");

const appendChat = (chats, message) => {
  const li = document.createElement("li");
  li.innerText = message;
  chats.appendChild(li);
};

wsClientOne.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);

  if (data.type === "error") {
    clientOneStatus.innerText = data.message;
  }
  if (data.type === "server-response") {
    clientOneStatus.innerText = data.message;
  }
  if (data.type === "chat") {
    appendChat(clientOneChat, `${data.username}: ${data.message}`);
  }
};

wsClientTwo.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);

  if (data.type === "error") {
    clientTwoStatus.innerText = data.message;
  }
  if (data.type === "server-response") {
    clientTwoStatus.innerText = data.message;
  }
  if (data.type === "chat") {
    appendChat(clientTwoChat, `${data.username}: ${data.message}`);
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
    type: "user_reg",
    username: username,
  });
  ws.send(registerMessage);
};

const sendChat = (ws, sender, recipient, message) => {
  const chatMessage = JSON.stringify({
    type: "chat",
    username: sender,
    recipient: recipient,
    message: message,
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
