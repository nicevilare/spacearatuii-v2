function buscar(){
    const param ={
        longitude : document.getElementById("longitude").value,
        latitude : document.getElementById("latitude").value,
        dateInicio : document.getElementById("dateInicio").value,
        dateFim : document.getElementById("dateFim").value        
    }
    fetch('/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: param
    })
    .then(response => {
        console.log(response)
        response.json()})    
    .catch((error) => {
        console.error('Erro:', error);
    });


}


