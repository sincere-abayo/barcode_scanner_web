// Get elements
const openModalBtn = document.getElementById('openModalBtn');
const closeModalBtn = document.getElementById('closeModalBtn');
const productModal = document.getElementById('productModal');

// Open modal
openModalBtn.addEventListener('click', () => {
  productModal.classList.remove('hidden');
});

// Close modal
closeModalBtn.addEventListener('click', () => {
  productModal.classList.add('hidden');
});

// Close modal when clicking outside
window.addEventListener('click', (event) => {
  if (event.target === productModal) {
    productModal.classList.add('hidden');
  }
});

// // Handle form submission (optional)
// document.getElementById('productForm').addEventListener('submit', (event) => {
//   event.preventDefault();
//   const productName = document.getElementById('productName').value;
//   const productType = document.getElementById('productType').value;
//   const productOwner = document.getElementById('productOwner').value;

//   console.log('Product Name:', productName);
//   console.log('Product Type:', productType);
//   console.log('Product Owner:', productOwner);

//   // You can add additional logic here to handle the form data, such as sending it to a server

//   // Close modal after submission
//   productModal.classList.add('hidden');
// });
