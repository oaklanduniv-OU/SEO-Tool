document.addEventListener('DOMContentLoaded', function() {
    // Fetch the list of level 1 directories in /templates/lighthouse_reports/
    fetch('/get-level-1-dirs')
      .then(response => response.json())
      .then(directories => {
        directories.sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
        const submenu = document.getElementById('SectionSelect');
        directories.forEach(dir => {
          const listItem = document.createElement('option');
          listItem.textContent=dir
          listItem.value=dir
          submenu.appendChild(listItem);
        });
      })
      .catch(error => {
        console.error('Error fetching directories:', error);
      });
  });

  document.getElementById('SectionSelect').addEventListener('change', function() {
    const selectedValue = this.value;

    if (selectedValue) {
        console.log('User selected:', selectedValue);
        // You can add more logic here as needed
    } else {
        console.log('No option selected.');
    }
});