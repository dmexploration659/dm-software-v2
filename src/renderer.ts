import axios from 'axios';
import './index.css';

const btnGetValFromDjango = document.getElementById('btn_get_val_from_django');

btnGetValFromDjango.onclick = async () => {
	try {
		const inputValue = (document.getElementById('input_text') as HTMLInputElement).value;

		const res = await axios.get('http://127.0.0.1:8000/edtwExampleAPI/get_val_from/', {
			params: { input: inputValue },
		});

		const result = res.data;

		// Convert the result object into a readable JSON string
		document.getElementById('p_output').innerHTML = `
            <strong>Input:</strong> ${result.input} <br>
            <strong>Length:</strong> ${result.length} <br>
            <strong>Message:</strong> ${result.message}
        `;
	} catch (error) {
		console.error('Error fetching data:', error);

		// Handle error response
		if (error.response) {
			document.getElementById('p_output').innerHTML = `
                <strong>Error:</strong> ${error.response.data.error} <br>
                <strong>Status:</strong> ${error.response.status}
            `;
		} else {
			document.getElementById('p_output').innerHTML =
				'<strong>Error:</strong> Could not connect to Django server.';
		}
	}
};
