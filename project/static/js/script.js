let parsedData = [];
const urlParams = new URLSearchParams(window.location.search);
const SourceURLParam = urlParams.get('sourceURL');
const RealURLParam = urlParams.get('realURL');

async function fetchAndParseReport() {
  const response = await fetch('/static/reports/linkchecker/linkchecker-report.txt');
  const text = await response.text();
  const blocks = text.split(/\n(?=URL\s+)/g);

  parsedData = blocks.map(block => {
    const url = matchField(block, /URL\s+`([^`]+)'/);
    const parent = matchField(block, /Parent URL\s+(.+?)(?:,|$)/);
    const realUrl = matchField(block, /Real URL\s{3}(.*?)(?=\s*(Check time|Size|Result))/);
    const resultError = matchField(block, /Result\s+Error:\s+(.+)/);
    const resultValid = /Result\s+Valid/i.test(block);
    const resultOk = /Result\s+OK/i.test(block);

    const status = resultError
      ? "broken"
      : resultValid || resultOk
      ? "valid"
      : "unknown";

    const message = resultError
      ? resultError
      : resultValid
      ? "Valid link"
      : "No result line";

    return {
      url,
      parent,
      realUrl,
      status,
      message,
    };
  });

  generateReport(parsedData); // Initial render
}

function matchField(text, regex) {
  const match = text.match(regex);
  return match ? match[1].trim() : null;
}

function getUrlLevel(url) {
  const path = new URL(url).pathname;
  // Filter out empty segments to avoid counting trailing slashes
  const segments = path.split('/').filter(Boolean);
  return segments.length;
}

function generateReport(data, sortBy = "count", showPageLevel = "level-all") {
  const linkList = document.getElementById("link-list");
  linkList.innerHTML = ""; // Clear previous output

  // Group by parent URL
  const grouped = {};

  data.forEach(link => {
    if (!link.parent) return;
    if (!grouped[link.parent]) {
      grouped[link.parent] = [];
    }
    // Include all links (not just broken ones)
    grouped[link.parent].push(link);
  });

  // Convert grouped object to array for sorting
  const groupedArray = Object.entries(grouped);

  switch (sortBy) {
    case "az":
      groupedArray.sort((a, b) => a[0].localeCompare(b[0]));
      break;
    case "za":
      groupedArray.sort((a, b) => b[0].localeCompare(a[0]));
      break;
    case "count":
    default:
      groupedArray.sort((a, b) => b[1].length - a[1].length);
      break;
  }

  var advFilteredArray = []
  switch (showPageLevel) {
    case "level-1":

      groupedArray.forEach(([parentUrl, children]) => {
        if (getUrlLevel(parentUrl) === 1) {
          advFilteredArray.push([parentUrl, children])
          
        }
      });
      break;
  
    case "level-2":

      groupedArray.forEach(([parentUrl, children]) => {
        if (getUrlLevel(parentUrl) === 2) {
          advFilteredArray.push([parentUrl, children])
          
        }
      });
      break;
  
    case "level-3":

      groupedArray.forEach(([parentUrl, children]) => {
        if (getUrlLevel(parentUrl) >= 3) {
          advFilteredArray.push([parentUrl, children])
    
        }
      });
      break;
  
    case "level-all":
    default:

      advFilteredArray = groupedArray
      break;
  }

  let totalLinks = 0;

  advFilteredArray.forEach(([parentUrl, links]) => {
    totalLinks += links.length;

    const wrapper = document.createElement("details");
    wrapper.className = "link-item grouped";
    const summary = document.createElement("summary");
    summary.innerHTML = `<span class="link-url">${parentUrl}</span> <span class="status-label">Total Links: ${links.length}</span>`;
    wrapper.appendChild(summary);

    const detailContent = document.createElement("div");
    detailContent.className = "link-details";

    links.forEach(link => {
      const block = document.createElement("div");
      block.classList.add("child-link");
      block.dataset.url = link.url;  // Set data-url
      block.dataset.realUrl = link.realUrl;  // Set data-real-url

      block.innerHTML = ` 
        <p><strong>URL:</strong> <a href="${link.url}" target="_blank">${link.url}</a></p>
        <p><strong>Real URL:</strong> <a href="${link.realUrl}" target="_blank">${link.realUrl}</a></p>
        <p><strong>Result:</strong> ${link.message}</p>
        <hr>
      `;

      detailContent.appendChild(block);
    });

    wrapper.appendChild(detailContent);
    linkList.appendChild(wrapper);
  });

  // Update total link count
  console.log(totalLinks)
  updateLinkCounts(totalLinks);
}

function updateLinkCounts(totalLinks) {
  // Update only the total link count
  document.getElementById("total-count").textContent = totalLinks;
}

function setupSearchFilters() {
  const parentInput = document.getElementById("search-parent");
  const urlInput = document.getElementById("search-url");
  const searchBtn = document.getElementById("search-btn");
  const resetBtn = document.getElementById("reset-btn");

  // Search by Parent URL and URL/Real URL
  const filterLinks = () => {
    const parentQuery = parentInput.value.toLowerCase();  // For Parent URL search
    const urlQuery = urlInput.value.toLowerCase();  // For URL/Real URL search

    const parentGroups = document.querySelectorAll(".link-item");

    let totalLinks = 0;

    parentGroups.forEach(group => {
      const summaryText = group.querySelector("summary")?.innerText.toLowerCase() || "";
      const parentMatches = parentQuery ? summaryText.includes(parentQuery) : true;  // Parent match condition

      let anyVisible = false;
      const childLinks = group.querySelectorAll(".child-link");

      childLinks.forEach(child => {
        const url = child.dataset.url?.toLowerCase() || "";
        const realUrl = child.dataset.realUrl?.toLowerCase() || "";

        // Check for URL or Real URL matches
        const urlMatches = urlQuery ? (url.includes(urlQuery) || realUrl.includes(urlQuery)) : true;

        const matches = parentMatches && urlMatches;

        child.style.display = matches ? "block" : "none";
        if (matches) anyVisible = true;
        group.style.display = anyVisible ? "block" : "none";
      if (anyVisible) totalLinks++;
      });

      
    });

    updateLinkCounts(totalLinks);
  };

  // Button and Enter key listeners
  searchBtn.addEventListener("click", filterLinks);
  parentInput.addEventListener("keydown", e => {
    if (e.key === "Enter") filterLinks();
  });
  urlInput.addEventListener("keydown", e => {
    if (e.key === "Enter") filterLinks();
  });

  // Reset button
  resetBtn.addEventListener("click", () => {
    parentInput.value = "";
    urlInput.value = "";
    const parentGroups = document.querySelectorAll(".link-item");
    parentGroups.forEach(g => g.style.display = "block");

    updateLinkCounts(parsedData.length-2);  // Reset to total links count
  });
}

document.addEventListener("DOMContentLoaded", () => {
  fetchAndParseReport();

  const sortSelect = document.getElementById("sort-select");
  const pageLevelSelect = document.getElementById("pageLevel-select");
  sortSelect.addEventListener("change", (e) => {
    generateReport(parsedData, e.target.value, pageLevelSelect.value);
  });

  
  pageLevelSelect.addEventListener("change", (e) => {
    console.log(sortSelect.value)
    generateReport(parsedData, sortSelect.value, e.target.value);
  });

  setupSearchFilters();
  if(SourceURLParam != null){
    document.getElementById("search-parent").value = SourceURLParam
    let searchButton = document.getElementById("search-btn")
    setTimeout(() => {
      searchButton.click();
    }, 100); // Can be 0, but 100ms ensures event listeners are ready
  
  }
});




