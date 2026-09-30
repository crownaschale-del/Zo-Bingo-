const tg = window.Telegram.WebApp;

// Start Telegram Mini App
tg.ready();
tg.expand();

// Get Telegram user
const user = tg.initDataUnsafe?.user;

const usernameElement = document.getElementById("username");

if (user) {
    usernameElement.textContent =
        user.first_name || "Telegram User";
} else {
    usernameElement.textContent =
        "Telegram User";
}

// Create Bingo board
const board = document.getElementById("board");

for (let i = 1; i <= 25; i++) {

    const number = document.createElement("div");

    number.className = "number";
    number.textContent = i;

    number.addEventListener("click", function () {

        number.classList.toggle("selected");

    });

    board.appendChild(number);
}

// Start game button
const startButton = document.getElementById("startBtn");

startButton.addEventListener("click", function () {

    document.getElementById("message").textContent =
        "🎮 Game started!";

    tg.HapticFeedback.impactOccurred("medium");
});