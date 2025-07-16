/*document.addEventListener('DOMContentLoaded', function() {
    // Fetch the list of level 1 directories in /templates/lighthouse_reports/
    fetch('/get-level-1-dirs')
      .then(response => response.json())
      .then(directories => {
        directories.sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
        const submenu = document.getElementById('report-submenu');
        directories.forEach(dir => {
          const listItem = document.createElement('li');
          const link = document.createElement('a');
          link.href = `/reports/${dir}/section-overview.html`; // Link to section-overview.html
          link.textContent = dir;
          listItem.appendChild(link);
          submenu.appendChild(listItem);
        });
      })
      .catch(error => {
        console.error('Error fetching directories:', error);
      });
  });
*/

  