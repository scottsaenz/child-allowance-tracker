// filepath: /child-allowance-tracker/child-allowance-tracker/static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    const expenditureForm = document.getElementById('expenditure-form');
    
    if (expenditureForm) {
        expenditureForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(expenditureForm);
            const data = {};
            formData.forEach((value, key) => {
                data[key] = value;
            });

            fetch('/api/expenditures', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('Network response was not ok.');
            })
            .then(data => {
                alert('Expenditure added successfully!');
                expenditureForm.reset();
            })
            .catch(error => {
                console.error('There was a problem with the fetch operation:', error);
                alert('Failed to add expenditure. Please try again.');
            });
        });
    }

    const fetchExpenditures = () => {
        fetch('/api/expenditures')
            .then(response => response.json())
            .then(data => {
                const expenditureList = document.getElementById('expenditure-list');
                expenditureList.innerHTML = '';
                data.forEach(expenditure => {
                    const listItem = document.createElement('li');
                    listItem.textContent = `${expenditure.date}: $${expenditure.amount} - ${expenditure.description}`;
                    expenditureList.appendChild(listItem);
                });
            })
            .catch(error => console.error('Error fetching expenditures:', error));
    };

    fetchExpenditures();
});