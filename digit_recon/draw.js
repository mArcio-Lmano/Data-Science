// draw.js
document.addEventListener("DOMContentLoaded", function () {
    // Get the canvas element
    var canvas = document.getElementById("drawCanvas");

    if (!canvas.getContext) {
        console.error("Canvas not supported!");
        return;
    }

    // Get the 2D drawing context
    var context = canvas.getContext("2d");

    // Set initial drawing properties
    context.lineWidth = 5;
    context.strokeStyle = "#000";

    // Flag to indicate whether to draw
    var isDrawing = false;

    // Event listeners for mouse actions
    canvas.addEventListener("mousedown", startDrawing);
    canvas.addEventListener("mousemove", draw);
    canvas.addEventListener("mouseup", stopDrawing);
    canvas.addEventListener("mouseout", stopDrawing);

    function startDrawing(e) {
        isDrawing = true;
        context.beginPath();
        context.moveTo(e.clientX - canvas.getBoundingClientRect().left, e.clientY - canvas.getBoundingClientRect().top);
    }

    function draw(e) {
        if (!isDrawing) return;

        context.lineTo(e.clientX - canvas.getBoundingClientRect().left, e.clientY - canvas.getBoundingClientRect().top);
        context.stroke();
    }

    function stopDrawing() {
        isDrawing = false;
        context.closePath();
    }

    var clearButton = document.getElementById("clearButton");
    clearButton.addEventListener("click", clearDrawing);

    function clearDrawing() {
        context.clearRect(0, 0, canvas.width, canvas.height);
    }

    var printButton = document.getElementById("printButton");
    printButton.addEventListener("click", printAndRescale);

    function printAndRescale() {
        // Get the drawing data URL from the canvas
        var dataURL = canvas.toDataURL();

        // Create an image element to load the drawing
        var img = new Image();
        img.onload = function () {
            // Create a new canvas with a size of 28x28 pixels
            var scaledCanvas = document.createElement("canvas");
            scaledCanvas.width = 28;
            scaledCanvas.height = 28;

            // Scale and draw the image onto the new canvas
            var scaledContext = scaledCanvas.getContext("2d");
            scaledContext.drawImage(img, 0, 0, 28, 28);

            // Open a new window and print the scaled drawing
            var printWindow = window.open();
            printWindow.document.write("<img src='" + scaledCanvas.toDataURL() + "' alt='Scaled Drawing'>");
        };

        // Set the source of the image to the drawing data URL
        img.src = dataURL;
    }
});
