// levelDisplay.js
import { getUserLevelData, calculateAndUpdateUserLevel } from './levelcalculator.js';

// Initialize the level display on the dashboard
export async function initializeLevelDisplay(userId) {
    try {
        // First, calculate and update the user's level
        await calculateAndUpdateUserLevel(userId);
        
        // Then fetch the updated level data
        const levelData = await getUserLevelData(userId);
        
        // Update the display
        updateLevelDisplay(levelData);
        
        // Add level icon to the dashboard
        createLevelIcon(levelData.level);
        
        console.log("Level display initialized with data:", levelData);
    } catch (error) {
        console.error("Error initializing level display:", error);
    }
}

// Update level display in the dashboard
function updateLevelDisplay(levelData) {
    // Create or update the level element in the stats section
    const statsSection = document.querySelector('.stats');
    
    if (statsSection) {
        // Check if the level card already exists
        let levelCard = document.getElementById('level-card');
        
        if (!levelCard) {
            // Create a new level card
            levelCard = document.createElement('div');
            levelCard.id = 'level-card';
            levelCard.className = 'stat-card';
            statsSection.appendChild(levelCard);
        }
        
        // Update the level card content
        levelCard.innerHTML = `
            <h3>User Level</h3>
            <p><span id="user-level">${levelData.level}</span></p>
            <div class="level-progress">
                <div class="level-progress-bar" style="width: ${(levelData.points % 500) / 5}%"></div>
            </div>
            <p class="points-info">${levelData.points % 500} / 500 points to next level</p>
        `;
    }
}

// Create a level icon in the top right corner
function createLevelIcon(level) {
    // Check if the level icon already exists
    let levelIcon = document.getElementById('level-icon');
    
    if (!levelIcon) {
        // Create a new level icon
        levelIcon = document.createElement('div');
        levelIcon.id = 'level-icon';
        levelIcon.className = 'level-icon';
        
        // Add level icon to the main element
        const main = document.querySelector('.main');
        if (main) {
            main.appendChild(levelIcon);
        }
    }
    
    // Update the level icon content
    levelIcon.innerHTML = `
        <div class="level-badge">
            <span class="level-number">${level}</span>
        </div>
    `;
    
    // Add hover effect to show more info
    levelIcon.addEventListener('mouseenter', () => {
        const existingTooltip = levelIcon.querySelector('.level-tooltip');
        if (!existingTooltip) {
            const levelTooltip = document.createElement('div');
            levelTooltip.className = 'level-tooltip';
            levelTooltip.textContent = `Level ${level}`;
            levelIcon.appendChild(levelTooltip);
        }
    });
    
    levelIcon.addEventListener('mouseleave', () => {
        const tooltip = levelIcon.querySelector('.level-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    });
}