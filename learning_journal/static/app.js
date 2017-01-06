$(document).ready(function(){
    form = $("#new_entry_form");
    form.submit(function(e){
        e.preventDefault();
        $.ajax({
            type: 'POST',
            url: '/',
            data: form.serialize(),
            success: function(e){
                console.log("created new entry");
                href = $('div.entries.container a:first-of-type').attr('href').split('/').slice(1)
                console.log(href)
                href[href.length - 1]++
                href = '/' + href.join('/')
                $("div.entries.container").prepend('<article><h6 class="date">'+ $("#date").val() +'</h6><section><a href="'+ href +'"><h4>'+ $('.title_input').val() +'</h4></a></section></article>')
                $(".title_input").val("")
                $("#new_entry_form textarea").val("")
            }
        });
    });
});