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

    // Highlight matching number
    const cells = document.querySelectorAll(".number");

    cells.forEach(cell => {

        if (cell.textContent == number) {
            cell.classList.add("selected");
        }

    });

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

// Add CALL NUMBER button
const callButton = document.createElement("button");

callButton.textContent = "🎱 CALL NUMBER";

callButton.addEventListener("click", callNumber);

startButton.after(callButton);

// Create first card
generateBingoCard();
