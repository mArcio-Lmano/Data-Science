document.addEventListener("DOMContentLoaded", function () {
    var canvas = document.getElementById("drawCanvas");
  
    if (!canvas.getContext) {
      console.error("Canvas not supported!");
      return;
    }
  
    var context = canvas.getContext("2d");
  
    // Set initial drawing properties
    context.lineWidth = 25;
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
    printButton.addEventListener("click", classifyImage);
  
    async function classifyImage() {
        var dataURL = canvas.toDataURL();
      
        // Extract the base64-encoded image data
        var imageData = dataURL.split(",")[1];
      
        // Send the drawing data to the server as JSON
        await fetch("/classifyImage", {
          method: "POST",
          headers: {
            "Content-Type": "application/json", // Use application/json for JSON data
          },
          body: JSON.stringify({
            data: {
              drawing: imageData,
            },
          }),
        })
          .then((response) => response.text())
          .then((result) => {
            console.log("Result from server:", result);
      
            const resultContainer = document.getElementById("resultContainer");
            
            // Display the result in the HTML element
            resultContainer.textContent = "Number: " + result;
          })
          .catch((error) => {
            console.error("Error sending data to server:", error);
          });
      }
  });
  