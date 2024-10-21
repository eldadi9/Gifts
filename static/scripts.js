function markReceived(personId) {
    fetch('/mark_received', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: personId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Gift marked as received for ' + personId);
            // עדכון הממשק המשתמש אם צריך
            // לדוגמה, שינוי צבע השורה או עדכון כיתוב
        } else {
            alert('Error marking gift as received.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
