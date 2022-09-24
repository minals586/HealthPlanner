$(document).ready(function () {
        // example: https://getbootstrap.com/docs/4.2/components/modal/
        // show modal
        $('#rest-modal').on('show.bs.modal', function (event) {
            const button = $(event.relatedTarget) // Button that triggered the modal
            const RestaurantID = button.data('source') // Extract info from data-* attributes

            const RestaurantName = button.data('RestaurantName') // Extract info from data-* attributes
            const Address = button.data('Address')
            const CustomerID = button.data('CustomerID')

    
            const modal = $(this)
            if (RestaurantID === 'New Restaurant') {
                modal.find('.modal-title').text(RestaurantID)
                $('#rest-form-display').removeAttr('RestaurantID')
            } else {
                modal.find('.modal-title').text('Edit Restaurant ' + RestaurantID)
                $('#rest-form-display').attr('RestaurantID', RestaurantID)
            }
    
            if (RestaurantName) {
                modal.find('.form-RestaurantName').val(RestaurantName);
            } else {
                modal.find('.form-RestaurantName').val("");
            }

            if (Address) {
                modal.find('.form-Address').val(Address);
            } else {
                modal.find('.form-Address').val("");
            }
        })
    
    
        $('#submit-rest').click(function () {
            const RestaurantID = $('#rest-form-display').attr('RestaurantID');
            const RestaurantName = $('#rest-modal').find('.form-RestaurantName').val();
            const Address = $('#rest-modal').find('.form-Address').val();
            const CustomerID = $('#rest-form-display').attr('CustomerID');
            $.ajax({
                type: 'POST',
                url: RestaurantID ? '/edit/' + RestaurantID : '/create',
                contentType: 'application/json;charset=UTF-8',
                data: JSON.stringify({
                    'CustomerID': CustomerID,
                    'RestaurantName': RestaurantName,
                    'Address': Address
                }),
                success: function (res) {
                    console.log(res.response)
                    location.reload();
                },
                error: function () {
                    console.log('Error');
                }
            });
        });
    
        $('.remove').click(function () {
            const remove = $(this)
            $.ajax({
                type: 'POST',
                url: '/delete/' + remove.data('source'),
                success: function (res) {
                    console.log(res.response)
                    location.reload();
                },
                error: function () {
                    console.log('Error');
                }
            });
        });

        $('#go-home').click(function () {
            window.open('/index', '_self')
        });

        $('#exercise-query').click(function () {
            window.open('/exercise-query', '_self')
        });

        $('#get-personalized-plan').click(function () {
            window.open('/get-personalized-plan', '_self')
        });

        $('#food-query').click(function () {
            window.open('/food-query', '_self')
        });
    
});