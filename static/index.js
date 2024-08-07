document.getElementById('paymentForm').addEventListener('submit', function (event) {
    event.preventDefault();

    const amount = document.getElementById('amount').value;
    const currency = document.getElementById('currency').value;
    const paymentMethod = document.getElementById('paymentMethod').value;
    const derivAccount = document.getElementById('derivAccount').value;

    // Make a request to your Flask server to process the payment
    makePayment(amount, currency, paymentMethod, derivAccount);
});

function makePayment(amount, currency, paymentMethod, derivAccount) {
    // Replace this URL with the actual URL of your Flask server
    const serverUrl = 'http://localhost:8800/process-payment';

    fetch(serverUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            amount: amount,
            currency: currency,
            paymentMethod: paymentMethod,
            derivAccount: derivAccount,
        }),
    })
        .then((response) => response.json())
        .then((result) => {
            const resultElement = document.getElementById('result');
            const messagesElement = document.getElementById('messages');

            // Clear previous messages
            messagesElement.innerHTML = '';

            if (result.error) {
                // Display error.message in your UI.
                console.log(result.error.message);
            } else {
                // The payment has succeeded. Display a success message.
                console.log(result);
                // create success message
                const div = document.createElement('div');
                // add p element
                div.innerHTML = `
                    <p>Payment of ${amount} Successful</p>
                `;

                // append to document
                messagesElement.appendChild(div);
            }
        })
        .catch((error) => {
            console.log(error);
        });
}
