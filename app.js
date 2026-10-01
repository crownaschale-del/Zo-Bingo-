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

const playerName =
    user?.first_name || "Player";

usernameElement.textContent =
    playerName;


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

let currentRound = 0;

let joinedRound = null;


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
// GENERATE CARD
// ==========================================

function generateBingoCard() {

    board.innerHTML = "";

    cardNumbers = [];

    const numbers = [];

    for (let i = 1; i <= 75; i++) {

        numbers.push(i);

    }


    numbers.sort(
        () => Math.random() - 0.5
    );


    for (let i = 0; i < 25; i++) {

        const cell =
            document.createElement("div");

        cell.className = "number";


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


    updateCardMarks();

}


// ==========================================
// JOIN CURRENT ROUND
// ==========================================

async function joinRound() {

    if (joinedRound === currentRound) {

        return;

    }


    try {

        const response =
            await fetch(
                API_URL + "/api/join",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        player_name:
                            playerName,

                        card:
                            cardNumbers

                    })

                }
            );


        const data =
            await response.json();


        if (data.success) {

            joinedRound =
                currentRound;

            message.textContent =
                "✅ Card registered! " +
                "Waiting for game to start...";

        }

        else {

            message.textContent =
                "⚠️ " + data.message;

        }

    }

    catch (error) {

        console.log(error);

        message.textContent =
            "❌ Connection error.";

    }

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


            if (number === "FREE") {

                return;

            }


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


        // Save server state

        currentRound =
            data.round;

        calledNumbers =
            data.called_numbers || [];


        // ==================================
        // NEW ROUND
        // ==================================

        if (
            joinedRound !== currentRound &&
            data.status === "picking"
        ) {

            // Generate a new card

            generateBingoCard();

            // Join the round

            await joinRound();

        }


        // ==================================
        // MARK CALLED NUMBERS
        // ==================================

        updateCardMarks();


        // ==================================
        // PICKING
        // ==================================

        if (
            data.status === "picking"
        ) {

            message.textContent =
                "🎯 Card selection: " +
                data.remaining +
                " seconds";

        }


        // ==================================
        // PLAYING
        // ==================================

        else if (
            data.status === "playing"
        ) {

            const lastNumber =
                calledNumbers[
                    calledNumbers.length - 1
                ];


            if (lastNumber) {

                message.textContent =
                    "🎱 Called: " +
                    getLetter(lastNumber) +
                    "-" +
                    lastNumber;

            }

            else {

                message.textContent =
                    "🎮 Game started!";

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
// INITIAL CARD
// ==========================================

generateBingoCard();


// ==========================================
// START GAME STATUS CHECKING
// ==========================================

getGameStatus();


// Check every second

setInterval(
    getGameStatus,
    1000
);
