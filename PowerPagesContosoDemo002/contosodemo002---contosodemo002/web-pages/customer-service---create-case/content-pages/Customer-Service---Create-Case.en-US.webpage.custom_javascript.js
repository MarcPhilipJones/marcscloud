(function ($) {
      $(document).ready(function () {
        // Autopopulate customerid field with user's account and primarycontactid field with user's contact
        var accountId = $("#case-user-account").val();
        var accountName = $("#case-user-account-name").val();
        var contactId = $("#case-user-contact").val();
        var contactName = $("#case-user-contact-name").val();
        if (accountId != null)
        {
          $("#customerid").val(accountId);
          $("#customerid_name").val(accountName);
          $("#customerid_entityname").val("account");
          $("#customerid").trigger("change");
          $("#primarycontactid").val(contactId);
          $("#primarycontactid_name").val(contactName);
          $("#primarycontactid_entityname").val("contact");
          $("#primarycontactid").trigger("change");
        }
      function primarycontactidValidation() {
        // disable primarycontactid if customer is an account
        if ($("#customerid_name").val() == "" || $("#customerid_entityname").val() == "contact")
        {
          $("#primarycontactid").val('');
          $("#primarycontactid_name").val('');
          $("#primarycontactid").trigger("change");
          $("#primarycontactid_name").attr("disabled", true);
          $("#primarycontactid_name").parent().find('.input-group-btn').hide();
        }
        else
        {
          $("#primarycontactid_name").removeAttr("disabled");
          $("#primarycontactid_name").parent().find('.input-group-btn').show();
        }
        }
        primarycontactidValidation();
        $("#customerid").on("change",primarycontactidValidation);
      });
    }(jQuery));