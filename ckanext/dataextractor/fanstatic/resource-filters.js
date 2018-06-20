 $(document).ready(function () {

    // Mark all existing checkboxes in the nearest table
    $('.mark-all').click(function (e) {

        var table = $(e.target).closest('table');
        $('td input:checkbox', table).prop('checked', this.checked);

    });

 });