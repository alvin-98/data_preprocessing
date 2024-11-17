class ThemeManager {
  constructor() {
    this.theme = localStorage.getItem("theme") || "light";
    this.initialize();
  }

  initialize() {
    document.documentElement.setAttribute("data-theme", this.theme);
    document.querySelector("html").setAttribute("data-theme", this.theme);
    this.createToggleButton();
  }

  createToggleButton() {
    const button = document.createElement("button");
    button.className = "theme-toggle";
    button.setAttribute("aria-label", "Toggle theme");
    button.innerHTML = this.theme === "light" ? "🌙" : "☀️";
    button.addEventListener("click", () => this.toggleTheme());
    document.body.appendChild(button);
  }

  toggleTheme() {
    this.theme = this.theme === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", this.theme);
    document.querySelector("html").setAttribute("data-theme", this.theme);
    localStorage.setItem("theme", this.theme);
    const button = document.querySelector(".theme-toggle");
    button.innerHTML = this.theme === "light" ? "🌙" : "☀️";
  }
}

class DataProcessor {
  constructor() {
    this.currentDataType = null;
    this.themeManager = new ThemeManager();
    this.initializeEventListeners();
  }

  initializeEventListeners() {
    // Data type selection
    const typeButtons = document.querySelectorAll(".btn-type");
    typeButtons.forEach((button) => {
      button.addEventListener("click", () =>
        this.handleDataTypeSelection(button)
      );
    });

    // Form submissions
    document
      .getElementById("uploadForm")
      .addEventListener("submit", (e) => this.handleUpload(e));
    document
      .getElementById("imageProcessForm")
      .addEventListener("submit", (e) => this.handleProcess(e));
    document
      .getElementById("textProcessForm")
      .addEventListener("submit", (e) => this.handleProcess(e));
    document
      .getElementById("audioProcessForm")
      .addEventListener("submit", (e) => this.handleProcess(e));
  }

  handleDataTypeSelection(button) {
    // Remove selection from all buttons
    document.querySelectorAll(".btn-type").forEach((btn) => {
      btn.classList.remove("selected");
    });

    // Select current button
    button.classList.add("selected");
    this.currentDataType = button.dataset.type;

    // Show upload section
    document.getElementById("uploadSection").classList.remove("hidden");

    // Update file input accept attribute
    const fileInput = document.getElementById("file");
    if (this.currentDataType === "image") {
      fileInput.accept = "image/*";
    } else if (this.currentDataType === "text") {
      fileInput.accept = ".txt,.doc,.docx";
    } else if (this.currentDataType === "audio") {
      fileInput.accept = "audio/*,.wav,.mp3,.ogg";
    }

    // Hide all process sections and results
    document.getElementById("imageProcessSection").classList.add("hidden");
    document.getElementById("textProcessSection").classList.add("hidden");
    document.getElementById("audioProcessSection").classList.add("hidden");
    document.getElementById("resultsSection").classList.add("hidden");
    document.getElementById("originalContent").classList.add("hidden");
    document.getElementById("processedContent").innerHTML = "";
  }

  async handleUpload(e) {
    e.preventDefault();
    try {
      const formData = new FormData();
      const fileInput = document.getElementById("file");

      if (!fileInput.files[0]) {
        throw new Error("Please select a file");
      }

      formData.append("file", fileInput.files[0]);
      formData.append("type", this.currentDataType);

      const response = await fetch("/upload/", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.file_path) {
        this.showProcessingOptions(data.file_path);
      } else {
        throw new Error("No file path received from server");
      }
    } catch (error) {
      this.showError(`Upload failed: ${error.message}`);
    }
  }

  async handleProcess(e) {
    e.preventDefault();
    try {
      const selectedActions = Array.from(
        document.querySelectorAll(
          `#${this.currentDataType}ProcessForm input[name="actions"]:checked`
        )
      ).map((cb) => cb.value);

      if (selectedActions.length === 0) {
        throw new Error("Please select at least one modification");
      }

      const contentDisplay = document
        .getElementById("originalContent")
        .querySelector(".content-display");

      // Get file path based on data type
      let filePath;
      if (this.currentDataType === "image") {
        filePath = contentDisplay.querySelector("img").dataset.path;
      } else if (this.currentDataType === "audio") {
        filePath = contentDisplay.querySelector("audio").dataset.path;
      } else {
        filePath = contentDisplay.dataset.path;
      }

      if (!filePath) {
        throw new Error("No file path found");
      }

      const formData = new FormData();
      formData.append("file_path", filePath);
      selectedActions.forEach((action) => formData.append("actions", action));
      formData.append("type", this.currentDataType);

      const response = await fetch("/process/", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.error || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      if (data.processed_images && data.processed_images.length > 0) {
        this.displayProcessedContent(data.processed_images);
      } else {
        throw new Error("No processed content received from server");
      }
    } catch (error) {
      this.showError(`Processing failed: ${error.message}`);
    }
  }

  showProcessingOptions(filePath) {
    // Hide all process sections initially
    document.getElementById("imageProcessSection").classList.add("hidden");
    document.getElementById("textProcessSection").classList.add("hidden");
    document.getElementById("audioProcessSection").classList.add("hidden");

    // Show the appropriate process section
    const processSection = `${this.currentDataType}ProcessSection`;
    document.getElementById(processSection).classList.remove("hidden");

    // Show results section and original content
    document.getElementById("resultsSection").classList.remove("hidden");
    const originalContent = document.getElementById("originalContent");
    originalContent.classList.remove("hidden");
    const contentDisplay = originalContent.querySelector(".content-display");

    if (this.currentDataType === "image") {
      contentDisplay.innerHTML = `<img src="${filePath}" alt="Original" class="image" data-path="${filePath}">`;
    } else if (this.currentDataType === "audio") {
      contentDisplay.innerHTML = `
        <audio controls class="audio-player" data-path="${filePath}">
          <source src="${filePath}" type="audio/wav">
          Your browser does not support the audio element.
        </audio>
        <div class="audio-info"></div>
      `;
    } else {
      contentDisplay.dataset.path = filePath;
      this.fetchAndDisplayText(filePath, contentDisplay);
    }
  }

  async fetchAndDisplayText(filePath, element) {
    try {
      const response = await fetch(`/view_content/?path=${filePath}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.content) {
        element.textContent = data.content;
      } else {
        throw new Error("No content received from server");
      }
    } catch (error) {
      this.showError(`Error loading text content: ${error.message}`);
    }
  }

  displayProcessedContent(results) {
    const container = document.getElementById("processedContent");
    container.innerHTML = ""; // Clear previous results

    results.forEach((result) => {
      const div = document.createElement("div");
      div.className = "content-card";

      if (this.currentDataType === "image") {
        div.innerHTML = `
          <h3 class="content-title">${this.capitalizeFirst(result.action)}</h3>
          <img src="${result.file_path}" alt="${result.action}" class="image">
          <p class="content-description">${result.description}</p>
        `;
      } else if (this.currentDataType === "audio") {
        const durationChange = result.changes.duration_change.toFixed(2);
        const amplitudeChange = result.changes.amplitude_change.toFixed(2);

        div.innerHTML = `
          <h3 class="content-title">${this.capitalizeFirst(result.action)}</h3>
          <div class="audio-player-container">
            <audio controls class="audio-player">
              <source src="${result.file_path}" type="audio/wav">
              Your browser does not support the audio element.
            </audio>
          </div>
          <div class="content-stats">
            <h4>Changes Made:</h4>
            <ul>
              <li>Duration: ${
                durationChange > 0 ? "+" : ""
              }${durationChange}s</li>
              <li>Amplitude: ${
                amplitudeChange > 0 ? "+" : ""
              }${amplitudeChange}dB</li>
            </ul>
            <h4>Properties:</h4>
            <ul>
              <li>Duration: ${result.properties.duration.toFixed(2)}s</li>
              <li>Sample Rate: ${result.properties.sample_rate}Hz</li>
              <li>Channels: ${result.properties.channels}</li>
            </ul>
          </div>
          <p class="content-description">${result.description}</p>
        `;
      } else {
        // Create changes summary
        const changesList = result.changes
          .map(
            (change) =>
              `<li><span class="original">${
                change[0]
              }</span> → <span class="modified">${
                change[1] || "(removed)"
              }</span></li>`
          )
          .join("");

        const wordCountDiff =
          result.word_count.after - result.word_count.before;
        const wordCountText =
          wordCountDiff === 0
            ? "No change in word count"
            : `Word count ${
                wordCountDiff > 0 ? "increased" : "decreased"
              } by ${Math.abs(wordCountDiff)}`;

        div.innerHTML = `
          <h3 class="content-title">${this.capitalizeFirst(result.action)}</h3>
          <div class="content-stats">
            <p class="word-count">${wordCountText}</p>
            ${
              result.changes.length > 0
                ? `
              <div class="changes-list">
                <h4>Example Changes:</h4>
                <ul>${changesList}</ul>
              </div>
            `
                : ""
            }
          </div>
          <div class="content-display">${result.content}</div>
          <p class="content-description">${result.description}</p>
        `;
      }

      container.appendChild(div);
    });
  }

  showError(message) {
    console.error(message);
    alert(message);
  }

  capitalizeFirst(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }
}

// Initialize the app when the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new DataProcessor();
});
