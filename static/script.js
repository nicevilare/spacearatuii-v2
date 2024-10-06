function buscar() {
    const param = {
        longitude: document.getElementById("longitude").value,
        latitude: document.getElementById("latitude").value,
        dateInicio: document.getElementById("dateInicio").value,
        dateFim: document.getElementById("dateFim").value        
    }

    fetch('/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(param)  // Convert param to a JSON string
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        console.log(data);
    })
    .catch((error) => {
        console.error('Erro:', error);
    });
}


