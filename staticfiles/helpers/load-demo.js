$(document).ready(function () {

    $("#id_template").on("change", function () {

        if ($(this).val() != null) {

            $.ajax("demo")

        }

    });

});