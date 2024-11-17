import { UIHelper } from "../utils/UIHelper.js";

export class AudioProcessor {
  displayContent(contentDisplay, filePath) {
    contentDisplay.innerHTML = `
            <audio controls class="audio-player" data-path="${filePath}">
                <source src="${filePath}" type="audio/wav">
                Your browser does not support the audio element.
            </audio>
            <div class="audio-info"></div>
        `;
  }

  displayProcessedContent(div, result) {
    const durationChange = result.changes.duration_change.toFixed(2);
    const amplitudeChange = result.changes.amplitude_change.toFixed(2);

    div.innerHTML = `
            <h3 class="content-title">${UIHelper.capitalizeFirst(
              result.action
            )}</h3>
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
  }

  getFilePath(contentDisplay) {
    return contentDisplay.querySelector("audio").dataset.path;
  }
}
