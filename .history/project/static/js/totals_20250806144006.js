document.addEventListener("DOMContentLoaded", function () {
    var userSelectedSection =""
    document.getElementById('SectionSelect').addEventListener('change', function() {
        
        
        handleSectionSelectChange();
        fetchData();
        requestIdleCallback(() => {
            AverageGauges(); // Defer
        });
        
    });
    function handleSectionSelectChange() {
        const select = document.getElementById('SectionSelect');
        userSelectedSection = select.value;
    
       
    }

    

    function createGauge(name, score, path) {
        const percent = Math.round(score * 100);
        const circumference = 2 * Math.PI * 56;
        const arc = score * circumference;
        const dashArray = `${arc}, ${circumference}`;

        let rating = "lh-gauge__wrapper--fail";
        if (score >= 0.9) rating = "lh-gauge__wrapper--pass";
        else if (score >= 0.5) rating = "lh-gauge__wrapper--average";

        const wrapper = document.createElement("a");
        wrapper.className = `lh-gauge__wrapper ${rating}`;
        if (path != undefined) {
            wrapper.href = `/reports/${path}/#${name}`;
        }

        wrapper.innerHTML = `
            <div class="lh-gauge__svg-wrapper">
                <svg class="lh-gauge" viewBox="0 0 120 120">
                    <circle class="lh-gauge-base" r="56" cx="60" cy="60" stroke-width="8"></circle>
                    <circle class="lh-gauge-arc" r="56" cx="60" cy="60" stroke-width="8"
                        style="transform: rotate(-87.9537deg); stroke-dasharray: ${dashArray};">
                    </circle>
                </svg>
            </div>
            <div class="lh-gauge__percentage">${percent}</div>
            <div class="lh-gauge__label">${name.replace("-", " ")}</div>
        `;
        return wrapper;
    }

    const path = window.location.pathname;
    const match = path.match(/reports\/([^\/]+)/);
    const section = match ? match[1] : '';

    

    

    // Create childContainer for SEO List
    const childContainer = document.createElement("div");
    childContainer.className = "SEOListContainer";
    const paginationContainer = document.createElement("div");
    paginationContainer.id = "pagination"; // Add a container for pagination buttons
    childContainer.appendChild(paginationContainer);

    async function AverageGauges(){
        document.getElementById("AverageSEOScores").innerHTML =""
        const container = document.createElement("div");
        container.style.display = "flex";
        container.style.flexDirection = "column";
        container.style.alignItems = "center";
    
        const wrapper = document.createElement("div");
        wrapper.style.margin = "20px 0";
        wrapper.style.borderTop = "1px solid #ccc";
        wrapper.style.borderBottom = "1px solid #ccc";
        wrapper.style.padding = "10px";
    
        const contentBox = document.createElement("div");
        contentBox.style.paddingLeft = "10px";
    
        const scoresRow = document.createElement("div");
        scoresRow.className = "lh-scores-header";
        scoresRow.style.marginTop = "10px";
        wrapper.appendChild(contentBox);
    container.appendChild(wrapper);

    const targetContainer = document.getElementsByClassName("lh-scores-container")[0];
    if (targetContainer) {
        targetContainer.append(container);
    } else {
        console.warn("⚠️ Couldn't find .lh-scores-container to inject average scores.");
    }

    // Append childContainer to the DOM first before fetching data
    document.getElementsByClassName("lh-container")[0].appendChild(childContainer);

    // Fetch the average scores and append them directly
    try {
        let res;



        
        if (userSelectedSection == "" || userSelectedSection == "Home") {
        

            res = await fetch(`/api/average-scores?page=all`);
        } else {
            
            res = await fetch(`/api/average-scores/${userSelectedSection}?page=all`);
        }

        const dataAverage = await res.json();
        console.log(dataAverage);
        console.log("Averaged Lighthouse Scores:", dataAverage);

        const displayOrder = ["performance", "accessibility", "best-practices", "seo"];

        // Only display the averaged scores
        displayOrder.forEach((key) => {
            if (dataAverage.average[key] !== undefined) {
                scoresRow.appendChild(createGauge(key, dataAverage.average[key]));
            }
        });

        if (isHomepage()) {
            contentBox.innerHTML = "<p><em>Summary</em></p>";
        } else {
            contentBox.innerHTML = "<p><em>These are averaged from using this page's score as well as all child pages beneath it.</em></p>";
        }

        

        var lcSection
        
        (async () => {
            if(userSelectedSection == "Home"){
                lcSection = ""
            }
            else{
                lcSection = userSelectedSection + "/index.html"
            }

            const data = await fetchAndParseReport(lcSection, true);
const brokenLinks = data.filter(link => link.status === "broken");
const forbiddenLinks = data.filter(link => link.status === "403");
const totalBroken = brokenLinks.length;

console.log("Broken:", brokenLinks.length);
console.log("403s:", forbiddenLinks.length);
let lcScore;
let blTitle = "broken links: " + totalBroken;

// Thresholds
const isSitewide = lcSection === ""; // or however you’re determining sitewide
const maxExpectedBroken = 3000; // Adjust this based on your expectations

if (isSitewide) {
  // Dynamic scaling for large reports
  lcScore = 1 - (totalBroken / maxExpectedBroken);
  if (lcScore < 0) lcScore = 0; // Clamp to 0
} else {
  // Static scaling for individual pages
  lcScore = 1 - (totalBroken / 15);
  if (lcScore < 0) lcScore = 0; // Clamp to 0
}

scoresRow.appendChild(createGauge(blTitle, lcScore.toFixed(2), "/#"));
            


            

          })();
          contentBox.appendChild(scoresRow);
        let lcTotals = document.createElement("div")
        lcTotals.innerHTML = `<p>Total broken links found on this section : ${2}</p>`

    } catch (err) {
        console.error("Failed to fetch scores", err);
        contentBox.textContent = "Error fetching scores.";
    }
}

    // Declare `currentPage` and `totalPages` here to make them globally accessible in the script
    let currentPage = 1; // Initial page number
    let totalPages = 1;  // Will be updated with the API response
    const listPages = document.createElement("div");
    listPages.id = "SEOListPages-Container";

    // Fetch Data Function (to be called on pagination change)
    async function fetchData(section = "") {
        handleSectionSelectChange()
        console.log(userSelectedSection)
        if(isHomepage() && userSelectedSection != "Home"){
            var section = userSelectedSection;
        }
        else{
            var section = match ? match[1] : '';
        }
        

        
        listPages.innerHTML = "";  // Clear previous rows
        try {
            let res;
            
            if (section === "") {
                res = await fetch(`/api/average-scores?page=${currentPage}`);
            } else {
                
                res = await fetch(`/api/average-scores/${section}?page=${currentPage}`);
            }
            
            const data = await res.json();
            totalPages = data.pagination.total_pages; // Assuming the API provides this info

            // SEO page List
            data.pages.forEach((index) => {
                const row = document.createElement("div");
                row.className = "page-score-row";

                const pathDiv = document.createElement("div");
                pathDiv.style.flex = "1";
        
                
                pathDiv.innerHTML = `<a href="/static/reports/lighthouse_reports/${index.path}">/${index.path}</a>`;
                

                const gaugesDiv = document.createElement("div");
                gaugesDiv.className = "gauges";
                (async () => {
                    const data = await fetchAndParseReport(index.path ,false);
   
                    if (data && Array.isArray(data) && data.length > 0){
                        
                    let lcScore = 1 - data.length/15
                    let blTitle = "broken links: " + data.length
                    
                    if(data.length > 15){
                        gaugesDiv.appendChild(createGauge("broken links: 15+", "1", "/#"))
                    }
                    else{
                    gaugesDiv.appendChild(createGauge(blTitle, lcScore, "/#"))
                    }
                    
                    }
                    
                    else{
                        gaugesDiv.appendChild(createGauge("broken links: 0", "1", "/#"))
                    }

                  })();
                const displayOrder = ["broken Link", "performance", "accessibility", "best-practices", "seo"];
                displayOrder.forEach((key) => {
                    if (index.scores[key] !== undefined) {
                        gaugesDiv.appendChild(createGauge(key, index.scores[key], index.path));
                    }
                });

                row.appendChild(pathDiv);
                row.appendChild(gaugesDiv);
                listPages.appendChild(row);
                childContainer.appendChild(listPages);
            });

            // Create pagination controls
            createPaginationButtons();

        } catch (err) {
            console.error("Failed to fetch score list", err);
            const contentBox = document.getElementById("contentBox");
            contentBox.textContent = "Error fetching scores.";
        }
    }

    // Pagination buttons creation
    function createPaginationButtons() {
        const paginationContainer = document.getElementById("pagination");

        // Clear previous pagination buttons
        paginationContainer.innerHTML = "";

        // Previous Page Button
        const prevButton = document.createElement("button");
        prevButton.innerHTML = "<";
        prevButton.id = "prevPage-btn";
        prevButton.onclick = () => changePage(currentPage - 1);
        paginationContainer.appendChild(prevButton);

        // Page Number Input Field
        const pageInput = document.createElement("input");
        pageInput.type = "number";
        pageInput.value = currentPage;
        pageInput.min = 1;
        pageInput.max = totalPages;
        pageInput.style = `
            background-color: #877148;
            color: white;
            border-radius: 5px;
            border: 1px solid #555;
            cursor: pointer;
            transition: background-color 0.2s ease;
            width: 2rem;
        `;
        pageInput.onchange = () => {
            const page = parseInt(pageInput.value);
            if (page >= 1 && page <= totalPages) {
                changePage(page);
            }
        };
        paginationContainer.appendChild(pageInput);

        // Total Pages Display
        const totalPagesDisplay = document.createElement("span");
        totalPagesDisplay.innerText = ` of ${totalPages}`;
        paginationContainer.appendChild(totalPagesDisplay);

        // Next Page Button
        const nextButton = document.createElement("button");
        nextButton.innerHTML = ">";
        nextButton.id = "nextPage-btn";
        nextButton.onclick = () => changePage(currentPage + 1);
        paginationContainer.appendChild(nextButton);
    }

    // Handle page change
    function changePage(page) {
        if (page < 1 || page > totalPages) return; // Prevent invalid page numbers
        currentPage = page;
        fetchData();  // Fetch new data based on updated page
    }

    // Initially fetch data for page 1
    fetchData();
   // Run AverageGauges *non-blocking*, after paint
requestIdleCallback(() => {
    AverageGauges();
});
    

    // Helper function to check if it's the homepage
    function isHomepage() {
        const currentUrl = window.location.href;
        const baseUrl = window.location.origin;
        return currentUrl === baseUrl || currentUrl === baseUrl + '/';
    }


    function matchField(text, regex) {
        const match = text.match(regex);
        return match ? match[1].trim() : null;
      }
    let parsedData = [];

    async function fetchAndParseReport(pageURL, isAverage) {
        const response = await fetch('/static/reports/linkchecker/linkchecker-report.txt');
        const text = await response.text();
        const blocks = text.split(/\n(?=URL\s+)/g);
      
        const parsedData = blocks.map(block => {
          const url = matchField(block, /URL\s+`([^`]+)'/);
          const parent = matchField(block, /Parent URL\s+(.+?)(?:,|$)/);
          const realUrl = matchField(block, /Real URL\s{3}(.*?)(?=\s*(Check time|Size|Result))/);
          const resultError = matchField(block, /Result\s+Error:\s+(.+)/);
          const resultValid = /Result\s+Valid/i.test(block);
          const resultOk = /Result\s+OK/i.test(block);
      
          let status;
if (resultError) {
  if (resultError.includes("403")) {
    status = "403";
  } else if (resultError.includes("401")) {
    status = "401";
  } else {
    status = "broken";
  }
} else if (resultValid || resultOk) {
  status = "valid";
} else {
  status = "unknown";
}
      
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
      
        // Group links by parent URL
        const grouped = {};
        parsedData.forEach(link => {
          if (!link.parent) return;
          if (!grouped[link.parent]) {
            grouped[link.parent] = [];
          }
          grouped[link.parent].push(link);
        });
      
        let combineURL = "https://www.oakland.edu/" + pageURL.replace("index.html", "");
        if (!combineURL.endsWith("/")) {
          combineURL += "/";
        }
      
        if (!isAverage) {
          // Return links ONLY for the exact page
          return grouped[combineURL] || [];
        } else {
          // Return all links under this section (including subpages)
          let combinedLinks = [];
          for (let key in grouped) {
            if (key.startsWith(combineURL)) {
              combinedLinks = combinedLinks.concat(grouped[key]);
            }
          }
          return combinedLinks;
        }
      }
      

});
