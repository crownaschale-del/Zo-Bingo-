            if (!marked[row * 5 + col]) {
                complete = false;
            }
        }

        if (complete) {
            showBingo();
            return;
        }
    }

    // Columns
    for (let col = 0; col < 5; col++) {

        let complete = true;

        for (let row = 0; row < 5; row++) {
            if (!marked[row * 5 + col]) {
                complete = false;
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

// Show BINGO
function showBingo() {

    message.textContent = "🎉 BINGO! YOU WIN!";

    tg.HapticFeedback.notificationOccurred("success");

    alert("🎉 BINGO!\nCongratulations!");
}
// Add CALL NUMBER button
const callButton = document.createElement("button");

callButton.textContent = "🎱 CALL NUMBER";

callButton.addEventListener("click", callNumber);

startButton.after(callButton);

// Create first card
generateBingoCard();
