const puzzlePiece = document.querySelector(".puzzle-piece");
const puzzleContainer = document.querySelector(".puzzle-container");

const addHiddenInputs = () => {
    const form = document.querySelector("form");

    ["pos_x_answer", "pos_y_answer"].forEach((name) => {
        const input = document.createElement("input");
        input.type = "text";
        input.name = name;
        input.id = `puzzle_${name}`;
        input.placeholder = name
            .replace(/_/g, " ")
            .replace(/\b\w/g, (c) => c.toUpperCase());
        input.style.display = "none";
        form.appendChild(input);
    });
};
addHiddenInputs();

const inputPosX = document.querySelector('input[id="puzzle_pos_x_answer"]');
const inputPosY = document.querySelector('input[id="puzzle_pos_y_answer"]');

let isDragging = false;
let offsetX = 0;
let offsetY = 0;

function getClientPos(e) {
    if (e.touches && e.touches.length > 0) {
        return {
            x: e.touches[0].clientX,
            y: e.touches[0].clientY,
        };
    }
    return {
        x: e.clientX,
        y: e.clientY,
    };
}

const fillInput = (input) => {
    const pieceRect = puzzlePiece.getBoundingClientRect();
    const containerRect = puzzleContainer.getBoundingClientRect();
    const pieceWidth = puzzlePiece.offsetWidth;
    const pieceHeight = puzzlePiece.offsetHeight;

    const clientX = input ? input.x : pieceRect.left;
    const clientY = input ? input.y : pieceRect.top;

    let x = clientX - containerRect.left - offsetX;
    let y = clientY - containerRect.top - offsetY;

    x = Math.max(0, Math.min(x, containerRect.width - pieceWidth));
    y = Math.max(0, Math.min(y, containerRect.height - pieceHeight));

    puzzlePiece.style.left = `${x}px`;
    puzzlePiece.style.top = `${y}px`;

    inputPosX.value = Math.round(x);
    inputPosY.value = Math.round(y);
};
fillInput();

puzzlePiece.addEventListener("mousedown", startDrag);
puzzlePiece.addEventListener("touchstart", startDrag);

puzzleContainer.addEventListener("mousemove", onDrag);
puzzleContainer.addEventListener("touchmove", onDrag);

puzzleContainer.addEventListener("mouseup", endDrag);
puzzleContainer.addEventListener("mouseleave", endDrag);
puzzleContainer.addEventListener("touchend", endDrag);
puzzleContainer.addEventListener("touchcancel", endDrag);

function startDrag(e) {
    e.preventDefault(); // Prevents scroll on touch devices
    isDragging = true;
    document.body.style.userSelect = "none";

    const pieceRect = puzzlePiece.getBoundingClientRect();
    const pos = getClientPos(e);

    offsetX = pos.x - pieceRect.left;
    offsetY = pos.y - pieceRect.top;
}

function onDrag(e) {
    console.log("on drag", isDragging);
    if (!isDragging) return;
    const pos = getClientPos(e);
    fillInput({ x: pos.x, y: pos.y });
}

function endDrag(e) {
    if (!isDragging) return;
    isDragging = false;
    document.body.style.userSelect = "auto";
}
