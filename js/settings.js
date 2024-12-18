// Get the modal
const modal = document.getElementById("about-us-modal");
const closeModalBtn = document.getElementById("close-modal");
const aboutUsBtn = document.getElementById("about-us-btn");

const contactModal = document.getElementById('contact-us-modal');
    const contactUsBtn = document.getElementById('contact-us-btn');
    const closeContactModalBtn = document.getElementById('close-contact-modal');

console.log('About Us button:', aboutUsBtn);
console.log('Close button:', closeModalBtn);

// Open the modal when "About" is clicked
aboutUsBtn.onclick = function() {
    console.log('About Us button clicked');
    modal.style.display = "flex";  // Show the modal with flex to center it
}

// Close the modal when the close button (x) is clicked
closeModalBtn.onclick = function() {
    console.log('Close button clicked');
    modal.style.display = "none";  // Hide the modal
}

// Close the modal if the user clicks outside the modal content
window.onclick = function(event) {
    if (event.target == modal) {
        console.log('Clicked outside modal');
        modal.style.display = "none";  // Hide the modal
    }
}

contactUsBtn.onclick = function() {
    contactModal.style.display = "flex"; // Show the modal
}

// Close the Contact Us modal when the close button (x) is clicked
closeContactModalBtn.onclick = function() {
    contactModal.style.display = "none"; // Hide the modal
}
