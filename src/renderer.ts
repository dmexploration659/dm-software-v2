import axios from "axios";
import "./index.css";

const portsDropdown = document.getElementById("ports_dropdown") as HTMLSelectElement;
const inputField = document.getElementById("input_value") as HTMLTextAreaElement;
const sendButton = document.getElementById("send_button") as HTMLButtonElement;
const responseDisplay = document.getElementById("response_display") as HTMLDivElement;

// Function to fetch and update the dropdown with available ports
const fetchPorts = async () => {
  // Save the currently selected port before updating
  const previousSelection = portsDropdown.value;

  try {
    const res = await axios.get("http://127.0.0.1:8000/edtwExampleAPI/get-available-ports/");
    console.log("Fetched data:", res.data);

    const result = res.data;
    const ports = result.available_ports || [];

    // Clear existing options
    portsDropdown.innerHTML = ""; // Remove all existing options

    // Add default "Select a Port" option
    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = "Select a Port";
    portsDropdown.appendChild(defaultOption);

    if (ports.length > 0) {
      ports.forEach((port: string) => {
        const option = document.createElement("option");
        option.value = port;
        option.textContent = port;
        portsDropdown.appendChild(option);
      });

      // Restore previous selection if it still exists
      if (ports.includes(previousSelection)) {
        portsDropdown.value = previousSelection;
      }
    } else {
      const noPortsOption = document.createElement("option");
      noPortsOption.value = "";
      noPortsOption.textContent = "No Ports Found";
      portsDropdown.appendChild(noPortsOption);
    }
  } catch (error) {
    console.error("Error fetching ports:", error);
    portsDropdown.innerHTML = '<option value="">Error Fetching Ports</option>';
  }
};

// Function to send text from the textarea **and selected port** to the Django API
const sendText = async () => {
  const textValue = inputField.value.trim();
  const selectedPort = portsDropdown.value;

  if (!textValue) {
    alert("❌ Please enter some text before sending.");
    return;
  }

  if (!selectedPort) {
    alert("❌ Please select a port before sending.");
    return;
  }

  try {
    const res = await axios.post("http://127.0.0.1:8000/edtwExampleAPI/send_text/", {
      text: 'G18 ( Plane X,Z ) G21 ( Millimeter ) G90 ( Absolute ) G40 ( Cancel radius compensation ) G92 X0 Z0 ( Offset coordinate system ) ',
      port: 'COM3',
      // text: textValue,
      // port: selectedPort,

    });

    console.log("Response from server:", res.data);

    // Display API response in the HTML
    responseDisplay.innerHTML = `
      <strong>Server Response:</strong>
      <pre>${JSON.stringify(res.data, null, 2)}</pre>
    `;
  } catch (error) {
    console.error("Error sending text:", error);
    responseDisplay.innerHTML = `<strong>Error:</strong> Failed to send message.`;
  }
};

// Attach event listeners
portsDropdown.addEventListener("click", fetchPorts);
sendButton.addEventListener("click", sendText);
