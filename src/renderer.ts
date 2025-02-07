import axios from "axios";
import "./index.css";

const portsDropdown = document.getElementById("ports_dropdown") as HTMLSelectElement;
const inputField = document.getElementById("input_value") as HTMLTextAreaElement;
const sendButton = document.getElementById("send_button") as HTMLButtonElement;
// const cancelButton = document.getElementById("cancel_button") as HTMLButtonElement;
const responseDisplay = document.getElementById("response_display") as HTMLDivElement;

// Function to fetch and update available ports
const fetchPorts = async () => {
  const previousSelection = portsDropdown.value;

  try {
    const res = await axios.get("http://127.0.0.1:8000/edtwExampleAPI/get-available-ports/");
    console.log("Fetched data:", res.data);

    const result = res.data;
    const ports = result.available_ports || [];

    portsDropdown.innerHTML = ""; // Clear existing options
    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = "Select a Port";
    portsDropdown.appendChild(defaultOption);

    ports.forEach((port: string) => {
      const option = document.createElement("option");
      option.value = port;
      option.textContent = port;
      portsDropdown.appendChild(option);
    });

    if (ports.includes(previousSelection)) {
      portsDropdown.value = previousSelection;
    }
  } catch (error) {
    console.error("Error fetching ports:", error);
    portsDropdown.innerHTML = '<option value="">Error Fetching Ports</option>';
  }
};

// Function to send text (G-Code) to CNC machine
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

  // Disable Send and Enable Cancel
  sendButton.disabled = true;
  // cancelButton.disabled = false;

  try {
    const res = await axios.post("http://127.0.0.1:8000/edtwExampleAPI/send_text/", {
      text: textValue,
      port: selectedPort,
    });

    console.log("Response from server:", res.data);

    responseDisplay.innerHTML = `
      <strong>Server Response:</strong>
      <pre>${JSON.stringify(res.data, null, 2)}</pre>
    `;
  } catch (error) {
    console.error("Error sending text:", error);
    responseDisplay.innerHTML = `<strong>Error:</strong> Failed to send message.`;
  } finally {
    sendButton.disabled = false;
    // cancelButton.disabled = true;
  }
};

// Function to release the port
const cancelOperation = async () => {
  try {
    await axios.post("http://127.0.0.1:8000/edtwExampleAPI/release_port/");
    alert("Port released successfully.");
  } catch (error) {
    console.error("Error releasing port:", error);
    alert("❌ Failed to release the port.");
  } finally {
    sendButton.disabled = false;
    // cancelButton.disabled = true;
  }
};

// Attach event listeners
portsDropdown.addEventListener("click", fetchPorts);
sendButton.addEventListener("click", sendText);
// cancelButton.addEventListener("click", cancelOperation);
