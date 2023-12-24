const { spawn } = require("child_process");
const express = require("express");
const bodyParser = require("body-parser");
const fs = require("fs");
const app = express();

app.use(bodyParser.json()); // Parse JSON requests

app.use(express.static("public"));

console.log("Server Started");

app.post("/classifyImage", (req, res) => {
  console.log("Received a request to classify an image.");

  const imageData = req.body;
  // console.log("Image Data: ", imageData);

  // Step 2: Generate a JSON file with the provided data
  const jsonFileName = "input.json";
  fs.writeFileSync(jsonFileName, JSON.stringify(imageData));
  console.log("File Created: ", jsonFileName);

  // Step 3: Execute a Python script using the generated JSON file
  const python_process = spawn("python", ["classify_image.py", jsonFileName]);

  let result = "";

  // Step 4: Python script generates a text file
  python_process.stdout.on("data", (data) => {
    result += data.toString();
    // console.log("Python Result: ", result)
  });

  python_process.on("close", () => {
    // Step 5: Send the python information to the server
    console.log("Python closed")
    // Clean up: Remove the generated files
    fs.unlinkSync(jsonFileName);
    // Step 6: Send the result back to the client
    res.send(result);
  });

  python_process.on("error", (err) => {
    console.error("Error executing Python process:", err);
    res.status(500).send("Internal Server Error");
  });
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
