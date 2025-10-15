// Custom JavaScript for Playfast documentation

// Add copy button to code blocks
document.addEventListener('DOMContentLoaded', function() {
  // Initialize code copy buttons
  const codeBlocks = document.querySelectorAll('pre > code');

  codeBlocks.forEach(function(block) {
    // Add line numbers if not present
    if (!block.classList.contains('hljs-ln')) {
      // Line numbering logic here if needed
    }
  });

  // Add performance badges
  const perfKeywords = ['3x faster', '10x faster', 'high-performance', 'lightning-fast'];
  const paragraphs = document.querySelectorAll('p, li');

  paragraphs.forEach(function(p) {
    const text = p.textContent.toLowerCase();
    perfKeywords.forEach(function(keyword) {
      if (text.includes(keyword)) {
        p.classList.add('highlight-performance');
      }
    });
  });
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  });
});
