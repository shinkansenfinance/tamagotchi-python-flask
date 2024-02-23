document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll(".currency-clp").forEach(function(element) {
        var self = element
        self.onblur = function() {
            var numericValue = self.value.replace(/[^0-9]/g, '')
            self.value = "$ " + 
                (parseInt(numericValue, 10) || 0).toLocaleString("es-CL")
        }
    });
    document.querySelectorAll(".currency").forEach(function(element) {
        var self = element
        self.onblur = function() {
            var numericValue = self.value.replace(/[^0-9.]/g, '') || 0
            self.value = "$ " + parseFloat(numericValue, 10).toLocaleString()
        }
    });

    document.querySelectorAll(".rut").forEach(function(element) {
        var self = element
        self.onchange = self.onblur = function() {
            self.value = self.value.replace(/(\d{1,3})(\d{3})(\d{3})([kK\d])/, '$1.$2.$3-$4')
        }        
    });
    document.querySelectorAll(".random-int-value").forEach(function(element) {
        element.value = parseInt(Math.random() * 10000000)
        element.onblur()
    });    
}, false);
  