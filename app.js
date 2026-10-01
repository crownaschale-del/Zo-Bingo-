const API_URL = "https://zo-bingo.onrender.com";

const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();


// ==========================================
// USER
// ==========================================

const user = tg.initDataUnsafe?.user;

const usernameElement =
    document.getElementById("username");

if (user) {
    usernameElement.textContent =
        user.first_name || "Telegram User";
} else {
    usernameElement.textContent =
        "Telegram User";
}


// ==========================================
// ELEMENTS
// ==========================================

const board =
    document.getElementById("board");

const message =
    document.getElementById("message");


// ==========================================
// GAME VARIABLES
// ==========================================

let cardNumbers = [];

let calledNumbers = [];

let gameStatus = "";

let currentRound = 0;


// ==========================================
// BINGO LETTER
// ==========================================

function getLetter(number) {

    if (number <= 15) return "B";

    if (number <= 30) return "I";

    if (number <= 45) return "N";

    if (number <= 60) return "G";

    return "O";
}


// ==========================================
// GENERATE BINGO CARD
// ==========================================

function generateBingoCard() {

    board.innerHTML = "";

    cardNumbers = [];

    const numbers = [];

    for (let i = 1; i <= 75; i++) {

        numbers.push(i);

    }


    // Shuffle numbers

    numbers.sort(
        () => Math.random() - 0.5
    );


    // Create 25 cells

    for (let i = 0; i < 25; i++) {

        const cell =
            document.createElement("div");

        cell.className = "number";


        // FREE CENTER

        if (i === 12) {

            cell.textContent = "FREE";

            cell.classList.add("free");

            cardNumbers.push("FREE");

        }

        else {

            const number =
                numbers[i];

            cell.textContent =
                number;

            cardNumbers.push(
                number
            );

        }


        board.appendChild(cell);

    }


    // Mark numbers already called

    updateCardMarks();

}


// ==========================================
// UPDATE CARD MARKS
// ==========================================

function updateCardMarks() {

    const cells =
        document.querySelectorAll(
            ".number"
        );


    cells.forEach(
        (cell, index) => {

            const number =
                cardNumbers[index];


            // FREE square

            if (number === "FREE") {

                return;

            }


            // Check if server called number

            if (
                calledNumbers.includes(
                    Number(number)
                )
            ) {

                cell.classList.add(
                    "selected"
                );

            }

            else {

                cell.classList.remove(
                    "selected"
                );

            }

        }
    );

}


// ==========================================
// GET GAME STATUS
// ==========================================

async function getGameStatus() {

    try {

        const response =
            await fetch(
                API_URL +
                "/api/game-status"
            );


        const data =
            await response.json();


        if (!data.success) {

            return;

        }


        // Save server information

        currentRound =
            data.round;

        gameStatus =
            data.status;

        calledNumbers =
            data.called_numbers || [];


        // ==================================
        // MARK CARD
        // ==================================

        updateCardMarks();


        // ==================================
        // DISPLAY STATUS
        // ==================================

        if (
            data.status ===
            "picking"
        ) {

            message.textContent =
                "🎯 Choose your card • " +
                data.remaining +
                " seconds";

        }


        else if (
            data.status ===
            "playing"
        ) {

            const lastNumber =
                calledNumbers[
                    calledNumbers.length - 1
                ];


            if (lastNumber) {

                const letter =
                    getLetter(
                        lastNumber
                    );


                message.textContent =
                    "🎱 Called: " +
                    letter +
                    "-" +
                    lastNumber;

            }

        }


    }

    catch (error) {

        console.log(
            "Connection error:",
            error
        );

    }

}


// ==========================================
// REFRESH GAME STATUS
// ==========================================

// Check immediately

getGameStatus();


// Check every 1 second

setInterval(
    getGameStatus,
    1000
);


// ==========================================
// CREATE INITIAL CARD
// ==========================================

generateBingoCard();
