(function () {
  'use strict';
  var api = {
    get: function (action, params) {
      var api_ver = 3;
      var base_url = ckan.sandbox().client.endpoint;
      params = $.param(params);
      var url = base_url + '/api/' + api_ver + '/action/' + action + '?' + params;
      return $.getJSON(url);
    },
    post: function (action, data) {
      var api_ver = 3;
      var base_url = ckan.sandbox().client.endpoint;
      var url = base_url + '/api/' + api_ver + '/action/' + action;
      return $.post(url, JSON.stringify(data), "json");
    }
  };
  var sortSwitch = 0;
  var sortColumn = '';

  // startsWith polyfill for IE 11
  if (!String.prototype.startsWith) {
    String.prototype.startsWith = function (searchString, position) {
      position = position || 0;
      return this.indexOf(searchString, position) === position;
    };
  }

  $(document).ready(function () {

    var filterColValue;
    var filterOp;
    var filterValue;
    var filterInput;
    var formFilter;
    var formOperator;
    var formFilterValue;
    var formFilterValueStart;

    // CSV delimiter buttons handler
    var buttons = $('#download_csv').find(".delimiter-button");
    buttons.on('click', function () {
      var elem = $(this);
      $('#csv_delimiter').val(elem.attr('delimiter'));
    });

    $('.auto-select').click(function () {
      $(this).select();
    });

    var createFilterToggle = $(".btn-create-filter");
    var saveFilterToggle = $(".btn-save-filter");
    var editFilterToggle = $(".btn-edit-filter");
    var editFilterCancel = $(".btn-edit-filter-cancel");
    var dataExplorerFiltersApply = $('.btn-apply-filter');
    var dataExplorerFiltersReset = $('.btn-reset-filter');

    var dataExplorerFilterCreate = $(".data-explorer-filter-create");
    var dataExplorerFilterCreateForm = $(".data-explorer-filter-create form");
    var dataExplorerNoFilters = $(".data-explorer-no-filters");
    var dataExplorerActiveFilters = $('.data-explorer-active-filters');
    var dataExplorerFilters = $('.data-explorer-filters');
    var dataExplorerFilterOperators = $('.data-explorer-filter-operators');
    var dataExplorerFiltersToggle = $('.data-explorer-filters-toggle');
    var dataFilterColumnSelect = $('.data-filter-column-select');
    var dataFilterInputValue = $('.data-filter-input-value');
    var dataFilterInputValueStart = $('.data-filter-input-value-start');
    var dataFilterDate = $('.data-filter-date');
    // var dataFilterCalendarToggle = $('.data-filter-calendar-toggle');
    var dataExtractorIntervalToggle = $('#data-filter-interval-toggle');
    var dataExtractorIntervalToggleLabel = $('.btn-interval');
    var calendarOptions = {
      showOn: 'both',
      buttonText: "<span class='fa fa-calendar'></span>",
      showButtonPanel: true,
      dateFormat: "yy-mm-dd",
      // altField: dataFilterDate
    };

    function initializeDatePickers() {
      if ($('.data-filter-column-select').children(':selected').hasClass('filter-type-timestamp')) {
        dataFilterInputValue.datetimepicker(calendarOptions);
        dataFilterInputValueStart.datetimepicker(calendarOptions);
      } else if ($('.data-filter-column-select').children(':selected').hasClass('filter-type-date')) {
        dataFilterInputValue.datepicker(calendarOptions);
        dataFilterInputValueStart.datepicker(calendarOptions);
      }
    }

    function showDatePickers() {
      if ($('.data-filter-column-select').children(':selected').hasClass('filter-type-timestamp')) {
        if (dataExtractorIntervalToggle.prop('checked')) {
          dataFilterInputValueStart.datetimepicker('show');
        } else {
          dataFilterInputValue.datetimepicker('show');
        }

      } else if ($('.data-filter-column-select').children(':selected').hasClass('filter-type-date')) {
        if (dataExtractorIntervalToggle.prop('checked')) {
          dataFilterInputValueStart.datepicker('show');
        } else {
          dataFilterInputValue.datepicker('show');
        }
      }
    }

    createFilterToggle.click(function () {
      dataFilterInputValue.val('');
      dataFilterInputValueStart.val('');
      dataExtractorIntervalToggle.prop('checked', false);
      $('.data-filter-edit').parent().removeClass('edit');
      dataExplorerFilterCreate.removeClass('hidden');
      createFilterToggle.removeClass('hidden');
      $('.data-filter-interval-toggle').removeClass('hidden');
      editFilterToggle.addClass('hidden');
      saveFilterToggle.removeClass('hidden');

      $('.data-filter-column-select').prop('selected', false);
      $('[name="data-filter-operator"]').prop('checked', false);

      intervalModeOff();
      initializeDatePickers();
      showDatePickers();
    });

    function editModeOn() {
      dataExplorerFilterCreate.removeClass("hidden");
    }

    function editModeOff() {
      dataExplorerFilterCreate.addClass("hidden");
      $('.data-filter-edit').parent().removeClass('edit');
    }

    dataExplorerFiltersToggle.click(function () {
      dataExplorerFilters.toggleClass("hidden");
    });

    editFilterCancel.click(function () {
      editModeOff();
    });

    // Do the following when selecting items from .data-filter-column-select
    $('.data-filter-column-select').on('change', function (e) {
      // Check if the selected item is of type date
      if ($(this).children(':selected').hasClass('filter-type-date')) {

        initializeDatePickers();
        showDatePickers();

        // Show date picker on basic input/interval end input
        dataFilterInputValue.addClass('data-filter-date');

        // Show date picker for interval start value
        dataFilterInputValueStart.addClass('data-filter-date');
      }

      // Check if the selected item is of type timestamp
      else if ($(this).children(':selected').hasClass('filter-type-timestamp')) {

        initializeDatePickers();
        showDatePickers();

        // In any other case
      } else {
        // Apply to basic input field
        dataFilterInputValue.datepicker('hide');
        dataFilterInputValue.removeClass('data-filter-date');
        dataFilterInputValue.datepicker('destroy');
        dataFilterInputValue.val('');

        // Apply to interval start field
        dataFilterInputValueStart.datepicker('hide');
        dataFilterInputValueStart.removeClass('data-filter-date');
        dataFilterInputValueStart.datepicker('destroy');
        dataFilterInputValueStart.val('');
      }

    });

    dataExplorerFiltersApply.on('click', function (evt) {
      $('[name="filter-inputs"]').submit();
    });

    function applyToggleFilter() {
      var filterColumn = $('.data-filter-column-select').val();
      var operator = $('#data-filter-input-type').val();
      var start = $('.data-filter-input-value-start').val();
      var end = $('.data-filter-input-value').val();
      var intervalFilter = ''
      if (operator.startsWith('NOT')) {
        intervalFilter = filterColumn + '|' + 'NOT BETWEEN' + '|' + start + ' AND ' + end;
      } else {
        intervalFilter = filterColumn + '|' + 'BETWEEN' + '|' + start + ' AND ' + end;
      }

      dataExplorerActiveFilters.append(
        '<input type="hidden" name="applied-filters" value="' + intervalFilter + '"/>'
      );

      // We don't want to render any visible changes on the page until postback.
      // That is why the next two lines are commented out.

      // dataExplorerNoFilters.addClass('hidden');
      // dataExplorerFilterCreate.toggleClass('hidden');
    }

    function applyFilter() {
      var filterName = $('.data-filter-column-select').val();
      var filterOperator = $('[name="data-filter-operator"]:checked').val();
      var applyFilterValue = $('.data-filter-input-value').val();
      var _ = filterName + '|' + filterOperator + '|' + applyFilterValue;

      dataExplorerActiveFilters.append(
        '<input type="hidden" name="applied-filters" value="' + _ + '"/>'
      );

      // We don't want to render any visible changes on the page until postback.
      // That is why the next three lines are commented out.

      // dataExplorerNoFilters.addClass('hidden');
      // dataExplorerFilterCreate.toggleClass('hidden');
      // dataExplorerActiveFilters.removeClass('hidden');
    }

    function submitFiltersForm() {
      $('[name="filter-inputs"]').submit();
    }

    // Apply filters on creation
    saveFilterToggle.on('click', function (evt) {
      evt.preventDefault();
      $('.flash-messages', document.body).html('');

      var filter_selected = $('input[name=data-filter-operator]:checked', '.data-explorer-filter-operators').val();
      var column_selected = $('#data-filter-column-select-id :selected').text();
      var between_selected = $('#data-filter-interval-toggle').is(':checked');
      var data_filter_input_value_start = $('.data-filter-input-value-start').val();
      var data_filter_input_value = $('.data-filter-input-value').val();

      if (between_selected) {

        if (column_selected != 'No filters available' && data_filter_input_value_start && data_filter_input_value) {
          var betweenToggle = $('[name="data-filter-interval-toggle"]:checked').length;

          if (betweenToggle > 0)
            applyToggleFilter();
          else
            applyFilter();

          submitFiltersForm();
        } else {
          var msg = ckan.i18n.ngettext('Please select column and insert values.');
          ckan.notify('', msg, 'warning');
        }

      } else {

        if (filter_selected && column_selected != 'No filters available' && data_filter_input_value) {
          var betweenToggle = $('[name="data-filter-interval-toggle"]:checked').length;

          if (betweenToggle > 0)
            applyToggleFilter();
          else
            applyFilter();

          submitFiltersForm();
        } else {
          var msg = ckan.i18n.ngettext('Please select column, operator and insert value.');
          ckan.notify('', msg, 'warning');
        }

      }

    });

    function intervalModeOn() {
      dataExtractorIntervalToggleLabel.addClass('btn-success');
      dataExtractorIntervalToggle.parent().parent().find('.data-filter-interval-fields').removeClass('hidden');
      dataExplorerFilterOperators.addClass('hidden');
    }

    function intervalModeOff() {
      dataExtractorIntervalToggleLabel.removeClass('btn-success');
      dataExtractorIntervalToggle.parent().parent().find('.data-filter-interval-fields').addClass('hidden');
      dataExplorerFilterOperators.removeClass('hidden');
    }

    // Set Interval toggle
    $(document).on('change', dataExtractorIntervalToggle, function (e) {
      if (dataExtractorIntervalToggle.prop('checked')) {
        intervalModeOn();
      } else {
        intervalModeOff();
      }
    });

    dataExplorerFiltersReset.on('click', function (evt) {
      dataExplorerFilters.addClass("hidden");
      dataExplorerActiveFilters.empty();
      $('[name="filter-inputs"]').submit();
    });

    $('.data-sort-btn').on('click', function (evt) {
      evt.preventDefault();

      sortColumn = $(this).attr('data-sort-name');
      var input = $('[name="sort"]:eq(0)');
      if (input.length) {
        if (input[0].value.substr(-4).toLowerCase() == 'desc')
          sortSwitch = 1;
        else
          sortSwitch = 0;
      }

      var sortCriteria = '';
      if (sortSwitch === 0) {
        sortCriteria = 'desc';
      } else {
        sortCriteria = 'asc';
      }

      var sort_str = sortColumn + ', ' + sortCriteria;
      var form = $('[name="filter-inputs"]');
      if (input.length) {
        input.val(sort_str);
      } else {
        form.append('<input type="hidden" name="sort" value="' + sort_str + '" />');
      }

      form.submit();
    });

    $('.data-extract-btn').on('click', function (evt) {

      evt.preventDefault();

      var path = window.location.pathname;
      var resource_id = path.substring(path.lastIndexOf('/') + 1, path.length);
      var modalWell = $('#download_api .form-control');
      var format = $(this).attr('data-format');
      var inputs = $('[name="applied-filters"]');
      var delimiter = $('#csv_delimiter').val();
      var filters = [];
      inputs.each(function (idx, elem) {
        var _ = elem.value.split('|');
        filters.push({
          name: _[0],
          operator: _[1],
          value: _[2]
        });
      });

      var sortInput = $('[name="sort"]');
      if (sortInput.length)
        sortInput = sortInput[0].value;
      else
        sortInput = null;

      if (format.toLowerCase() === 'api') {
        var base_url = ckan.sandbox().client.endpoint + '/api/action/datastore_resource_search\n';
        var postData = {
          resource_id: resource_id,
          filters: filters,
          offset: 0,
          limit: $('.total-results').text()
        };
        if (sortInput)
          postData['sort'] = sortInput;

        var _ = 'POST ' + base_url + '' + JSON.stringify(postData, null, 2);
        modalWell.html(_);
        //modalWell.removeClass('hidden');
      } else if (format.toLowerCase() === 'csv') {
        postData = {
          'format': format,
          'filters': filters,
          'resource_id': resource_id
        };
        if (sortInput)
          postData['sort'] = sortInput;
        if (delimiter)
          postData['delimiter'] = delimiter;

        api.post('azure_blob_create', postData).done(
          function (data) {
            var link = document.createElement('a')
            $(link).attr('href', data.result);
            $(link).attr('download', data.result);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          });
      } else {
        postData = {
          'format': format,
          'filters': filters,
          'resource_id': resource_id
        };
        if (sortInput)
          postData['sort'] = sortInput;

        api.post('azure_blob_create', postData).done(
          function (data) {
            var link = document.createElement('a')
            $(link).attr('href', data.result);
            $(link).attr('download', data.result);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          });
      }

    });

    function operatorSelector(text) {
      var val = '';
      switch (text) {
        case '=':
          val = '#data-filter-operator-eq';
          break;
        case '<':
          val = '#data-filter-operator-lt';
          break;
        case '>':
          val = '#data-filter-operator-gt';
          break;
        case '<=':
          val = '#data-filter-operator-lte';
          break;
        case '>=':
          val = '#data-filter-operator-gte';
          break;
        case '!=':
          val = '#data-filter-operator-neq';
          break;
      }
      return val;
    }

    $(document).on("click", '.data-filter-edit', function (e) {

      e.preventDefault();
      editFilterCancel.removeClass("hidden");
      dataExtractorIntervalToggle.prop('checked', false);
      $('.data-filter-interval-toggle').addClass('hidden');
      dataExplorerActiveFilters.children('.pill').removeClass('edit');
      dataExplorerFilterCreate.removeClass('hidden');
      intervalModeOff();

      if (dataExplorerFilterCreate.hasClass('hidden')) {
        $(this).parent().removeClass('edit');
      } else {

        $(this).parent().addClass('edit');
        $(saveFilterToggle).addClass('hidden');
        $(editFilterToggle).removeClass('hidden');

        filterColValue = ($(this).parent().find('.data-filter-column-value'));
        filterOp = ($(this).parent().find('.data-filter-operator'));
        filterValue = ($(this).parent().find('.data-filter-value'));
        filterInput = $(this).parent().find('[name="applied-filters"]');
        formFilter = $('.data-filter-column-select');
        formOperator = $(operatorSelector(filterOp.text()));
        formFilterValue = $('.data-filter-input-value');
        formFilterValueStart = $('.data-filter-input-value-start');

        if (filterOp.text() == 'NOT BETWEEN' || filterOp.text() == 'BETWEEN') {

          dataExtractorIntervalToggle.prop('checked', true);
          intervalModeOn();
          // Set filter column value
          formFilter.val(filterColValue.text());
          // Set operator value
          $('#data-filter-input-type').val(filterOp.text());
          // Set filter values
          formFilterValueStart.val(filterValue.text().split(' AND ')[0]);
          formFilterValue.val(filterValue.text().split(' AND ')[1]);

        } else {
          // Set filter column value
          formFilter.val(filterColValue.text());
          // Set operator value
          formOperator.prop('checked', true);
          // Set filter value
          formFilterValue.val(filterValue.text());
        }
        initializeDatePickers();
        showDatePickers();
      }
    });

    // Update filter with edited values and re-submit the form
    $(editFilterToggle).on('click', function (e) {

      e.preventDefault();

      if (filterOp.text() == 'NOT BETWEEN' || filterOp.text() == 'BETWEEN') {

        if ($('#data-filter-input-type').val() && formFilterValueStart.val() && formFilterValue.val()) {

          // We don't want to render any visible changes on the page until postback.
          // That is why the next three lines are commented out.

          // filterColValue.text(formFilter.val());
          // filterOp.text($('#data-filter-input-type').val());
          // filterValue.text(formFilterValueStart.val() + ' AND ' + formFilterValue.val());
          filterInput.val(formFilter.val() + '|' + $('#data-filter-input-type').val() + '|' + formFilterValueStart.val() + ' AND ' + formFilterValue.val());

          // editFilterToggle.addClass('hidden');
          submitFiltersForm();

        } else {
          var msg = ckan.i18n.ngettext('Please select column and insert values.');
          ckan.notify('', msg, 'warning');
        }

      } else {

        if ($('input[name="data-filter-operator"]:checked').val() && formFilterValue.val()) {

          // We don't want to render any visible changes on the page until postback.
          // That is why the next three lines are commented out.

          // filterColValue.text(formFilter.val());
          // filterOp.text($('input[name="data-filter-operator"]:checked').val());
          // filterValue.text(formFilterValue.val());
          filterInput.val(formFilter.val() + '|' + $('input[name="data-filter-operator"]:checked').val() + '|' + formFilterValue.val());

          // editFilterToggle.addClass('hidden');
          submitFiltersForm();

        } else {
          var msg = ckan.i18n.ngettext('Please select column, operator and insert value.');
          ckan.notify('', msg, 'warning');
        }
      }

    });

    dataExplorerFilterCreateForm.submit(function (e) {
      /*
        Since we changed the logic for applying filters
        there's no need to do anything here
      */
    });

    // Make sure the Apply button for filters is only shown when there is at least one filter created,
    // however, this does not apply when filters have already been added and removed afterwards.
    function showHideApplyButton() {
      if (dataExplorerActiveFilters.children('span').length > 0) {
        dataExplorerFiltersApply.removeClass('hidden');
        dataExplorerFiltersReset.removeClass('hidden');
      }
    }

    // Required for appended elements in .data-explorer-active-filters!
    $(document).on("click", ".data-filter-remove", function (event) {
      event.preventDefault();
      $(this).parent().children('input').remove();

      // We don't want to render any visible changes on the page until postback.
      // That is why the next three lines are commented out.

      // if (dataExplorerActiveFilters.children().length < 1) {
      //   dataExplorerNoFilters.removeClass('hidden');
      // }

      submitFiltersForm();
    });
  });
})
($);