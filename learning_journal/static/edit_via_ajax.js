$.ajax({
    type: 'POST',
    url: '/journal/1/edit-entry',
    data: {
        'title': 'TITLE HERE',
        'body': 'BODY HERE',
        'edit_date': '2017-01-06'
    },
    success: function(){
        console.log("edited entry");
    }
});