$(document).ready(function(){
    form = $("#new_entry_form");
    form.submit(function(e){
        // send ajax request to delete this expense
        $.ajax({
            type: 'POST',
            url: 'journal/new-entry',
            data: form.serialize(),
            success: function(){
                console.log("created new entry");
            }
        });
        // delete the containing row
        this_row.animate({
            opacity: 0
        }, 500, function(){
            $(this).remove();
        })
        e.prevent_default();
    });
});