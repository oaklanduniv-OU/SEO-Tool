document.getElementById('run-script-btn').addEventListener('click', function() {
    fetch('/run-script', { method: 'POST' })
      .then(response => response.json())
      .then(data => {
        alert(data.message); // Display success/failure message
      })
      .catch(error => {
        console.error('Error:', error);
      });
  });