document.addEventListener("DOMContentLoaded", () => {
    const satellite1Dropdown = document.getElementById("satellite1");
    const satellite2Dropdown = document.getElementById("satellite2");
    const riskValueElement = document.querySelector(".risk-value");
    const generateButton = document.getElementById("generateButton");

    // Fetch satellite names from the backend
    async function fetchSatelliteNames() {
        try {
            const response = await fetch("/get_satellites");
            const data = await response.json();
            const allSatellites = data.satellites;
            populateDropdowns(allSatellites);
        } catch (error) {
            console.error("Error fetching satellite data:", error);
        }
    }

    // Populate dropdowns with satellite names
    function populateDropdowns(satellites) {
        satellites.forEach(name => {
            const option1 = new Option(name, name);
            const option2 = new Option(name, name);
            satellite1Dropdown.add(option1);
            satellite2Dropdown.add(option2);
        });
    }

    // Remove selected satellite from the other dropdown
    function handleSelectionChange(changedDropdown, otherDropdown) {
        const selectedValue = changedDropdown.value;

        for (let option of otherDropdown.options) {
            option.hidden = option.value === selectedValue;
        }

        // Reset selection if the selected option was hidden
        if (otherDropdown.value === selectedValue) {
            otherDropdown.value = "";
        }
    }

    // Update placeholders when a satellite is selected
    async function updatePlaceholder(dropdown, placeholderId) {
        const selectedValue = dropdown.value;
        const placeholder = document.getElementById(placeholderId);

        if (!selectedValue) {
            placeholder.innerHTML = "No satellite selected.";
            return;
        }

        // Show loading message
        placeholder.innerHTML = "Generating trajectory...";

        try {
            const response = await fetch("/generate_trajectory", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ satellite: selectedValue }),
            });

            const data = await response.json();

            if (data.image) {
                placeholder.innerHTML = `<img src="${data.image}" class="img-fluid" alt="${selectedValue} trajectory">`;
            } else {
                placeholder.innerHTML = `<span class="text-danger">Error: ${data.error}</span>`;
            }
        } catch (error) {
            placeholder.innerHTML = `<span class="text-danger">Failed to generate trajectory.</span>`;
            console.error("Error:", error);
        }
    }

    // Event listeners for selection change
    satellite1Dropdown.addEventListener("change", () => {
        handleSelectionChange(satellite1Dropdown, satellite2Dropdown);
        updatePlaceholder(satellite1Dropdown, "satellite1-placeholder");
    });

    satellite2Dropdown.addEventListener("change", () => {
        handleSelectionChange(satellite2Dropdown, satellite1Dropdown);
        updatePlaceholder(satellite2Dropdown, "satellite2-placeholder");
    });

    // Perform Risk Analysis
    generateButton.addEventListener("click", async () => {
        const satellite1 = satellite1Dropdown.value;
        const satellite2 = satellite2Dropdown.value;

        if (!satellite1 || !satellite2) {
            alert("Please select both satellites.");
            return;
        }

        // Show loading state
        riskValueElement.textContent = "Calculating...";

        try {
            const response = await fetch("/predict_risk", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ satellite1, satellite2 }),
            });

            const data = await response.json();

            if (data.risk !== undefined) {
                riskValueElement.textContent = `${data.risk}%`;
            } else {
                riskValueElement.textContent = "Error";
            }
        } catch (error) {
            console.error("Error:", error);
            riskValueElement.textContent = "Error";
        }
    });

    // Fetch and populate satellite names on page load
    fetchSatelliteNames();
});