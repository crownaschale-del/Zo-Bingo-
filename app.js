const API_URL = "http://127.0.0.1:8000";
const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

// Telegram user
const user = tg.initDataUnsafe?.user;
const usernameElement = document.getElementById("username");

if (user) {
    usernameElement.textContent = user.first_name || "Telegram User";
} else {
    usernameElement.textContent = "Telegram User";
}

const board = document.getElementById("board");
const message = document.getElementById("message");

let calledNumbers = [];

// Generate Bingo card
function generateBingoCard() {

    board.innerHTML = "";

    const numbers = [];

    for (let i = 1; i <= 75; i++) {
        numbers.push(i);
    }

    numbers.sort(() => Math.random() - 0.5);

    for (let i = 0; i < 25; i++) {

        const cell = document.createElement("div");
        cell.className = "number";

        if (i === 12) {
            cell.textContent = "FREE";
            cell.classList.add("free");
        } else {
            cell.textContent = numbers[i];

            cell.addEventListener("click", function () {
                cell.classList.toggle("selected");
            });
        }

        board.appendChild(cell);
    }
}

// Get Bingo letter
function getLetter(number) {

    if (number <= 15) return "B";
    if (number <= 30) return "I";
    if (number <= 45) return "N";
    if (number <= 60) return "G";

    return "O";
}

// Check Bingo
function checkBingo() {

    const cells = document.querySelectorAll(".number");

    const marked = [];

    cells.forEach((cell, index) => {
        marked[index] =
            cell.classList.contains("selected") ||
            cell.classList.contains("free");
    });

    // Check rows
    for (let row = 0; row < 5; row++) {

        let complete = true;

        for (let col = 0; col < 5; col++) {
            if (!marked[row * 5 + col]) {
                complete = false;
                break;
            }
        }

        if (complete) {
            showBingo();
            return;
        }
    }

    // Check columns
    for (let col = 0; col < 5; col++) {

        let complete = true;

        for (let row = 0; row < 5; row++) {
            if (!marked[row * 5 + col]) {
                complete = false;
                break;
            }
        }

        if (complete) {
            showBingo();
            return;
        }
    }

    // Diagonal 1
    if (
        marked[0] &&
        marked[6] &&
        marked[12] &&
        marked[18] &&
        marked[24]
    ) {
        showBingo();
        return;
    }

    // Diagonal 2
    if (
        marked[4] &&
        marked[8] &&
        marked[12] &&
        marked[16] &&
        marked[20]
    ) {
        showBingo();
    }
}

// Show Bingo
function showBingo() {

    message.textContent = "🎉 BINGO! YOU WIN!";

    tg.HapticFeedback.notificationOccurred("success");

    alert("🎉 BINGO!\nCongratulations!");
}

// Call random number
function callNumber() {

    if (calledNumbers.length >= 75) {
        message.textContent = "🎉 All 75 numbers have been called!";
        return;
    }

    let number;

    do {
        number = Math.floor(Math.random() * 75) + 1;
    } while (calledNumbers.includes(number));

    calledNumbers.push(number);

    const letter = getLetter(number);

    message.textContent =
        `🎱 Number called: ${letter}-${number}`;

    // Highlight matching card number
    const cells = document.querySelectorAll(".number");

    cells.forEach(cell => {

        if (cell.textContent == number) {
            cell.classList.add("selected");
        }

    });

    // Check Bingo AFTER marking the number
    checkBingo();

    tg.HapticFeedback.impactOccurred("medium");
}

// Start game
const startButton = document.getElementById("startBtn");

startButton.addEventListener("click", function () {

    calledNumbers = [];

    generateBingoCard();

    message.textContent =
        "🎮 Game started!";

    tg.HapticFeedback.impactOccurred("medium");
});

// CALL NUMBER button
const callButton = document.createElement("button");

callButton.textContent = "🎱 CALL NUMBER";

callButton.addEventListener("click", callNumber);

startButton.after(callButton);

// Generate first card
generateBingoCard();
