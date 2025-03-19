// levelDisplayModule.js
import { getUserLevelData, calculateAndUpdateUserLevel } from './levelcalculator.js';

// Initialize the level display on any page
export async function initializeLevelDisplay(userId) {
    try {
        // First, calculate and update the user's level
        await calculateAndUpdateUserLevel(userId);
        
        // Then fetch the updated level data
        const levelData = await getUserLevelData(userId);
        
        // Add level icon to the current page
        createLevelIcon(levelData.level);
        
        console.log("Level display initialized with data:", levelData);
        
        return levelData;
    } catch (error) {
        console.error("Error initializing level display:", error);
    }
}

// Create a level icon in the top right corner
export function createLevelIcon(level) {
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
        <h7 class="level-para">Level   </h7>
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