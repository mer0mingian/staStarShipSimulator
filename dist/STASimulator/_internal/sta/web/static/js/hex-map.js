/**
 * Hexagonal map renderer for STA Starship Simulator
 * Uses flat-top hexagons with axial coordinates (q, r)
 *
 * Coordinate System:
 * - Axial coordinates (q, r) where q is column, r is row
 * - Center hex is at (0, 0)
 * - Flat-top orientation (pointy sides on left/right)
 */

const HexMap = {
    // Configuration
    hexSize: 35,  // Radius of hex in pixels (center to corner)

    // LCARS-themed terrain colors
    terrainColors: {
        open: '#1a1a2e',
        planetary_gravity: '#2a2a1a',
        dust_cloud: '#2a3a4a',
        debris_field: '#3a2a1a',
        asteroid_field: '#3a2a2a',
        dense_nebula: '#1a2a3a',
        stellar_gravity: '#4a3a1a',
    },

    // Terrain display names
    terrainNames: {
        open: 'Open Space',
        planetary_gravity: 'Planetary Gravity Well',
        dust_cloud: 'Dust Cloud',
        debris_field: 'Debris Field',
        asteroid_field: 'Asteroid Field',
        dense_nebula: 'Dense Nebula',
        stellar_gravity: 'Stellar Gravity Well',
    },

    // Terrain types that block visibility (ships hidden unless in same hex)
    visibilityBlockingTerrain: ['dust_cloud', 'dense_nebula'],

    // Terrain movement costs (Momentum to leave)
    terrainMovementCosts: {
        open: 0,
        planetary_gravity: 1,
        dust_cloud: 1,
        debris_field: 1,
        asteroid_field: 1,
        dense_nebula: 2,
        stellar_gravity: 2,
    },

    // Terrain types that are hazardous (damage if using Threat)
    hazardousTerrain: ['debris_field', 'asteroid_field'],

    /**
     * Convert axial coordinates to pixel position (flat-top hex)
     * @param {number} q - Column coordinate
     * @param {number} r - Row coordinate
     * @returns {{x: number, y: number}} Pixel position
     */
    axialToPixel(q, r) {
        const x = this.hexSize * (3/2 * q);
        const y = this.hexSize * (Math.sqrt(3)/2 * q + Math.sqrt(3) * r);
        return { x, y };
    },

    /**
     * Convert pixel position to axial coordinates
     * @param {number} x - X pixel position
     * @param {number} y - Y pixel position
     * @returns {{q: number, r: number}} Axial coordinates (rounded)
     */
    pixelToAxial(x, y) {
        const q = (2/3 * x) / this.hexSize;
        const r = (-1/3 * x + Math.sqrt(3)/3 * y) / this.hexSize;
        // Round to nearest hex
        return this.axialRound(q, r);
    },

    /**
     * Round fractional axial coordinates to nearest hex
     */
    axialRound(q, r) {
        // Convert to cube, round, convert back
        const x = q;
        const z = r;
        const y = -x - z;

        let rx = Math.round(x);
        let ry = Math.round(y);
        let rz = Math.round(z);

        const xDiff = Math.abs(rx - x);
        const yDiff = Math.abs(ry - y);
        const zDiff = Math.abs(rz - z);

        if (xDiff > yDiff && xDiff > zDiff) {
            rx = -ry - rz;
        } else if (yDiff > zDiff) {
            ry = -rx - rz;
        } else {
            rz = -rx - ry;
        }

        return { q: rx, r: rz };
    },

    /**
     * Generate SVG path for a hexagon centered at given position
     * @param {number} centerX - Center X pixel position
     * @param {number} centerY - Center Y pixel position
     * @returns {string} SVG path data
     */
    hexPath(centerX, centerY) {
        const corners = [];
        for (let i = 0; i < 6; i++) {
            // Flat-top: start angle at 0 degrees
            const angle = Math.PI / 3 * i;
            const px = centerX + this.hexSize * Math.cos(angle);
            const py = centerY + this.hexSize * Math.sin(angle);
            corners.push(`${px.toFixed(2)},${py.toFixed(2)}`);
        }
        return `M${corners.join('L')}Z`;
    },

    /**
     * Calculate hex distance between two coordinates
     */
    hexDistance(q1, r1, q2, r2) {
        return (Math.abs(q1 - q2) +
                Math.abs(q1 + r1 - q2 - r2) +
                Math.abs(r1 - r2)) / 2;
    },

    /**
     * Render the complete hex map
     * @param {string} containerId - DOM element ID to render into
     * @param {object} mapData - Map data with radius and tiles
     * @param {array} ships - Array of ship objects with positions
     * @param {object} options - Rendering options
     */
    render(containerId, mapData, ships, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }

        const radius = mapData?.radius || 3;
        const tiles = mapData?.tiles || [];
        const editable = options.editable || false;
        const onHexClick = options.onHexClick || null;
        const onShipClick = options.onShipClick || null;
        const selectedShipId = options.selectedShipId || null;
        const validMoves = options.validMoves || [];
        const shipLabelFontSize = options.shipLabelFontSize || 10;
        const coordFontSize = options.coordFontSize || 9;

        // Create tile lookup for terrain
        const tileLookup = {};
        tiles.forEach(tile => {
            if (tile.coord) {
                tileLookup[`${tile.coord.q},${tile.coord.r}`] = tile;
            }
        });

        // Calculate SVG dimensions
        const width = this.hexSize * (3 * radius + 2) + 80;
        const height = this.hexSize * Math.sqrt(3) * (2 * radius + 1) + 80;
        const centerX = width / 2;
        const centerY = height / 2;

        // Create SVG element
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', height);
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        svg.style.background = 'var(--lcars-bg, #000000)';
        svg.style.borderRadius = '10px';

        // Create defs for patterns
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');

        // Fog pattern for visibility-blocking terrain
        const fogPattern = document.createElementNS('http://www.w3.org/2000/svg', 'pattern');
        fogPattern.setAttribute('id', 'fog-pattern');
        fogPattern.setAttribute('patternUnits', 'userSpaceOnUse');
        fogPattern.setAttribute('width', '8');
        fogPattern.setAttribute('height', '8');

        // Diagonal lines for fog effect
        const fogLine1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        fogLine1.setAttribute('x1', '0');
        fogLine1.setAttribute('y1', '8');
        fogLine1.setAttribute('x2', '8');
        fogLine1.setAttribute('y2', '0');
        fogLine1.setAttribute('stroke', 'rgba(150, 180, 200, 0.4)');
        fogLine1.setAttribute('stroke-width', '2');
        fogPattern.appendChild(fogLine1);

        defs.appendChild(fogPattern);

        // Hindrance pattern for movement-cost terrain (dotted)
        const hindrancePattern = document.createElementNS('http://www.w3.org/2000/svg', 'pattern');
        hindrancePattern.setAttribute('id', 'hindrance-pattern');
        hindrancePattern.setAttribute('patternUnits', 'userSpaceOnUse');
        hindrancePattern.setAttribute('width', '6');
        hindrancePattern.setAttribute('height', '6');

        // Small dots for hindrance effect
        const hindranceDot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        hindranceDot.setAttribute('cx', '3');
        hindranceDot.setAttribute('cy', '3');
        hindranceDot.setAttribute('r', '1');
        hindranceDot.setAttribute('fill', 'rgba(204, 153, 102, 0.3)');
        hindrancePattern.appendChild(hindranceDot);

        defs.appendChild(hindrancePattern);

        // Hazard pattern for dangerous terrain (warning stripes)
        const hazardPattern = document.createElementNS('http://www.w3.org/2000/svg', 'pattern');
        hazardPattern.setAttribute('id', 'hazard-pattern');
        hazardPattern.setAttribute('patternUnits', 'userSpaceOnUse');
        hazardPattern.setAttribute('width', '10');
        hazardPattern.setAttribute('height', '10');
        hazardPattern.setAttribute('patternTransform', 'rotate(45)');

        const hazardStripe = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        hazardStripe.setAttribute('width', '5');
        hazardStripe.setAttribute('height', '10');
        hazardStripe.setAttribute('fill', 'rgba(204, 102, 102, 0.2)');
        hazardPattern.appendChild(hazardStripe);

        defs.appendChild(hazardPattern);
        svg.appendChild(defs);

        // Create groups for layering
        const hexGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        hexGroup.setAttribute('id', 'hex-tiles');

        const hindranceGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        hindranceGroup.setAttribute('id', 'hindrance-overlays');

        const fogGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        fogGroup.setAttribute('id', 'fog-overlays');

        const highlightGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        highlightGroup.setAttribute('id', 'hex-highlights');

        const shipGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        shipGroup.setAttribute('id', 'ships');

        // Get player ship position for showing terrain info on current hex
        const playerShip = ships?.find(s => s.faction === 'player');
        const playerPos = playerShip?.position || null;

        // Create valid move lookup
        const validMoveLookup = {};
        validMoves.forEach(move => {
            validMoveLookup[`${move.q},${move.r}`] = move.cost || 0;
        });

        // Render hexes
        for (let q = -radius; q <= radius; q++) {
            const r1 = Math.max(-radius, -q - radius);
            const r2 = Math.min(radius, -q + radius);
            for (let r = r1; r <= r2; r++) {
                const pos = this.axialToPixel(q, r);
                const px = centerX + pos.x;
                const py = centerY + pos.y;
                const key = `${q},${r}`;

                // Get tile data
                const tileData = tileLookup[key];
                const terrain = tileData?.terrain || 'open';

                // Create hex path
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', this.hexPath(px, py));
                path.setAttribute('fill', this.terrainColors[terrain] || this.terrainColors.open);
                path.setAttribute('stroke', 'var(--lcars-orange, #ff9900)');
                path.setAttribute('stroke-width', '1');
                path.setAttribute('data-q', q);
                path.setAttribute('data-r', r);
                path.setAttribute('data-terrain', terrain);
                path.classList.add('hex-tile');

                // Add hover effects
                path.addEventListener('mouseenter', () => {
                    path.setAttribute('stroke', 'var(--lcars-blue, #9999ff)');
                    path.setAttribute('stroke-width', '2');
                });
                path.addEventListener('mouseleave', () => {
                    const isHighlighted = path.classList.contains('valid-move');
                    if (isHighlighted) {
                        path.setAttribute('stroke', 'var(--lcars-green, #99cc99)');
                        path.setAttribute('stroke-width', '3');
                    } else {
                        path.setAttribute('stroke', 'var(--lcars-orange, #ff9900)');
                        path.setAttribute('stroke-width', '1');
                    }
                });

                // Click handler
                if (onHexClick) {
                    path.style.cursor = 'pointer';
                    path.addEventListener('click', (e) => {
                        e.stopPropagation();
                        onHexClick(q, r, terrain, validMoveLookup[key]);
                    });
                }

                hexGroup.appendChild(path);

                // Get terrain properties
                const movementCost = this.terrainMovementCosts[terrain] || 0;
                const isHazardous = this.hazardousTerrain.includes(terrain);
                const blocksVisibility = this.visibilityBlockingTerrain.includes(terrain);
                const isPlayerHere = playerPos && playerPos.q === q && playerPos.r === r;

                // Add hindrance overlay for movement-cost terrain (if NOT blocking visibility)
                // Visibility-blocking terrain shows fog instead
                if (movementCost > 0 && !blocksVisibility) {
                    const hindranceOverlay = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    hindranceOverlay.setAttribute('d', this.hexPath(px, py));
                    hindranceOverlay.setAttribute('fill', 'url(#hindrance-pattern)');
                    hindranceOverlay.setAttribute('stroke', 'none');
                    hindranceOverlay.setAttribute('pointer-events', 'none');
                    hindranceOverlay.classList.add('hindrance-overlay');
                    hindranceGroup.appendChild(hindranceOverlay);
                }

                // Add hazard overlay for dangerous terrain
                if (isHazardous) {
                    const hazardOverlay = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    hazardOverlay.setAttribute('d', this.hexPath(px, py));
                    hazardOverlay.setAttribute('fill', 'url(#hazard-pattern)');
                    hazardOverlay.setAttribute('stroke', 'none');
                    hazardOverlay.setAttribute('pointer-events', 'none');
                    hazardOverlay.classList.add('hazard-overlay');
                    hindranceGroup.appendChild(hazardOverlay);
                }

                // Add fog overlay for visibility-blocking terrain
                if (blocksVisibility) {
                    const fogOverlay = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    fogOverlay.setAttribute('d', this.hexPath(px, py));
                    fogOverlay.setAttribute('fill', 'url(#fog-pattern)');
                    fogOverlay.setAttribute('stroke', 'none');
                    fogOverlay.setAttribute('pointer-events', 'none');
                    fogOverlay.classList.add('fog-overlay');
                    fogGroup.appendChild(fogOverlay);
                }

                // Show movement cost indicator on hex (small text in corner)
                // For player's current hex, always show. For others, show if cost > 0
                if (movementCost > 0 && (isPlayerHere || !blocksVisibility)) {
                    const costIndicator = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    costIndicator.setAttribute('x', px + this.hexSize * 0.5);
                    costIndicator.setAttribute('y', py - this.hexSize * 0.4);
                    costIndicator.setAttribute('text-anchor', 'middle');
                    costIndicator.setAttribute('fill', isPlayerHere ? 'var(--lcars-orange, #ff9900)' : 'var(--lcars-tan, #cc9966)');
                    costIndicator.setAttribute('font-size', '9');
                    costIndicator.setAttribute('font-weight', 'bold');
                    costIndicator.textContent = `${movementCost}M`;
                    costIndicator.setAttribute('pointer-events', 'none');
                    highlightGroup.appendChild(costIndicator);
                }

                // Highlight valid moves
                if (validMoveLookup.hasOwnProperty(key)) {
                    path.setAttribute('stroke', 'var(--lcars-green, #99cc99)');
                    path.setAttribute('stroke-width', '3');
                    path.classList.add('valid-move');

                    // Show momentum cost if > 0
                    const cost = validMoveLookup[key];
                    if (cost > 0) {
                        const costText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                        costText.setAttribute('x', px);
                        costText.setAttribute('y', py + this.hexSize * 0.3);
                        costText.setAttribute('text-anchor', 'middle');
                        costText.setAttribute('fill', 'var(--lcars-tan, #cc9966)');
                        costText.setAttribute('font-size', '10');
                        costText.textContent = `${cost}M`;
                        highlightGroup.appendChild(costText);
                    }
                }

                // Show coordinates for center hex and debug mode
                if (options.showCoords || (q === 0 && r === 0)) {
                    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    text.setAttribute('x', px);
                    text.setAttribute('y', py - this.hexSize * 0.2);
                    text.setAttribute('text-anchor', 'middle');
                    text.setAttribute('fill', q === 0 && r === 0 ? 'var(--lcars-orange, #ff9900)' : '#444');
                    text.setAttribute('font-size', '9');
                    text.textContent = q === 0 && r === 0 ? 'CENTER' : `${q},${r}`;
                    highlightGroup.appendChild(text);
                }
            }
        }

        // Render ships
        if (ships && ships.length > 0) {
            ships.forEach((ship, index) => {
                if (!ship.position) return;

                const pos = this.axialToPixel(ship.position.q, ship.position.r);
                const px = centerX + pos.x;
                const py = centerY + pos.y;
                const isPlayer = ship.faction === 'player';
                const isSelected = selectedShipId === ship.id || selectedShipId === `enemy_${index}`;

                // Ship marker (triangle/chevron pointing up)
                const size = 12;
                const shipMarker = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
                const points = [
                    `${px},${py - size}`,
                    `${px - size * 0.866},${py + size * 0.5}`,
                    `${px + size * 0.866},${py + size * 0.5}`,
                ].join(' ');
                shipMarker.setAttribute('points', points);
                shipMarker.setAttribute('fill', isPlayer ? 'var(--lcars-green, #99cc99)' : 'var(--lcars-red, #cc6666)');
                shipMarker.setAttribute('stroke', isSelected ? '#ffffff' : '#000000');
                shipMarker.setAttribute('stroke-width', isSelected ? '3' : '2');
                shipMarker.setAttribute('data-ship-id', ship.id || (isPlayer ? 'player' : `enemy_${index}`));
                shipMarker.classList.add('ship-marker');

                if (onShipClick) {
                    shipMarker.style.cursor = 'pointer';
                    shipMarker.addEventListener('click', (e) => {
                        e.stopPropagation();
                        onShipClick(ship, index);
                    });
                }

                shipGroup.appendChild(shipMarker);

                // Ship name label
                const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                label.setAttribute('x', px);
                label.setAttribute('y', py + size + 14 + (shipLabelFontSize > 10 ? (shipLabelFontSize - 10) : 0));
                label.setAttribute('text-anchor', 'middle');
                label.setAttribute('fill', isPlayer ? 'var(--lcars-green, #99cc99)' : 'var(--lcars-red, #cc6666)');
                label.setAttribute('font-size', shipLabelFontSize);
                label.setAttribute('font-weight', 'bold');
                label.textContent = ship.name?.substring(0, 16) || (isPlayer ? 'Player' : `Enemy ${index + 1}`);
                shipGroup.appendChild(label);
            });
        }

        // Assemble SVG (order matters for layering)
        svg.appendChild(hexGroup);
        svg.appendChild(hindranceGroup);  // Hindrance under fog
        svg.appendChild(fogGroup);
        svg.appendChild(highlightGroup);
        svg.appendChild(shipGroup);

        // Clear container and add SVG
        container.innerHTML = '';
        container.appendChild(svg);

        // Store reference for later updates
        container._hexMapSvg = svg;
        container._hexMapData = { mapData, ships, options };

        return svg;
    },

    /**
     * Highlight valid movement destinations
     */
    highlightMoves(containerId, validCoords, color = 'var(--lcars-green, #99cc99)') {
        const container = document.getElementById(containerId);
        if (!container?._hexMapSvg) return;

        const hexGroup = container._hexMapSvg.querySelector('#hex-tiles');
        validCoords.forEach(coord => {
            const hex = hexGroup.querySelector(`[data-q="${coord.q}"][data-r="${coord.r}"]`);
            if (hex) {
                hex.setAttribute('stroke', color);
                hex.setAttribute('stroke-width', '3');
                hex.classList.add('valid-move');
            }
        });
    },

    /**
     * Clear all movement highlights
     */
    clearHighlights(containerId) {
        const container = document.getElementById(containerId);
        if (!container?._hexMapSvg) return;

        const hexGroup = container._hexMapSvg.querySelector('#hex-tiles');
        hexGroup.querySelectorAll('.valid-move').forEach(hex => {
            hex.setAttribute('stroke', 'var(--lcars-orange, #ff9900)');
            hex.setAttribute('stroke-width', '1');
            hex.classList.remove('valid-move');
        });

        // Also clear cost labels
        const highlightGroup = container._hexMapSvg.querySelector('#hex-highlights');
        highlightGroup.querySelectorAll('text').forEach(text => {
            if (text.textContent.endsWith('M')) {
                text.remove();
            }
        });
    },

    /**
     * Update ship positions without full re-render
     */
    updateShipPositions(containerId, ships) {
        const container = document.getElementById(containerId);
        if (!container?._hexMapData) return;

        // Re-render with updated ships
        const { mapData, options } = container._hexMapData;
        this.render(containerId, mapData, ships, options);
    },

    /**
     * Get terrain info for tooltip
     */
    getTerrainInfo(terrain) {
        const info = {
            name: this.terrainNames[terrain] || 'Unknown',
            cost: 0,
            hazardous: false,
            blocksVisibility: this.visibilityBlockingTerrain.includes(terrain),
        };

        switch (terrain) {
            case 'planetary_gravity':
                info.cost = 1;
                break;
            case 'dust_cloud':
                info.cost = 1;
                break;
            case 'debris_field':
                info.cost = 1;
                info.hazardous = true;
                break;
            case 'asteroid_field':
                info.cost = 1;
                info.hazardous = true;
                break;
            case 'dense_nebula':
                info.cost = 2;
                break;
            case 'stellar_gravity':
                info.cost = 2;
                break;
        }

        return info;
    },

    /**
     * Check if a terrain type blocks visibility
     */
    blocksVisibility(terrain) {
        return this.visibilityBlockingTerrain.includes(terrain);
    },

    /**
     * Render a legend panel explaining terrain overlays
     * @param {string} containerId - DOM element ID to render legend into
     */
    renderLegend(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const legendHtml = `
            <div class="hex-map-legend" style="
                background: rgba(0, 0, 0, 0.8);
                border: 1px solid var(--lcars-orange, #ff9900);
                border-radius: 5px;
                padding: 10px;
                font-size: 11px;
                color: var(--lcars-tan, #cc9966);
            ">
                <div style="font-weight: bold; color: var(--lcars-orange, #ff9900); margin-bottom: 8px;">
                    TERRAIN LEGEND
                </div>
                <div style="display: flex; flex-direction: column; gap: 6px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <svg width="20" height="20" style="flex-shrink: 0;">
                            <defs>
                                <pattern id="legend-fog" patternUnits="userSpaceOnUse" width="4" height="4">
                                    <line x1="0" y1="4" x2="4" y2="0" stroke="rgba(150, 180, 200, 0.6)" stroke-width="1"/>
                                </pattern>
                            </defs>
                            <rect width="20" height="20" fill="url(#legend-fog)" stroke="var(--lcars-blue, #9999ff)" stroke-width="1"/>
                        </svg>
                        <span>Low Visibility (ships hidden)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <svg width="20" height="20" style="flex-shrink: 0;">
                            <defs>
                                <pattern id="legend-hindrance" patternUnits="userSpaceOnUse" width="4" height="4">
                                    <circle cx="2" cy="2" r="1" fill="rgba(204, 153, 102, 0.5)"/>
                                </pattern>
                            </defs>
                            <rect width="20" height="20" fill="url(#legend-hindrance)" stroke="var(--lcars-tan, #cc9966)" stroke-width="1"/>
                        </svg>
                        <span>Movement Hindrance (costs Momentum)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <svg width="20" height="20" style="flex-shrink: 0;">
                            <defs>
                                <pattern id="legend-hazard" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
                                    <rect width="3" height="6" fill="rgba(204, 102, 102, 0.4)"/>
                                </pattern>
                            </defs>
                            <rect width="20" height="20" fill="url(#legend-hazard)" stroke="var(--lcars-red, #cc6666)" stroke-width="1"/>
                        </svg>
                        <span>Hazardous (damage if using Threat)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px; border-top: 1px solid #333; padding-top: 6px;">
                        <span style="color: var(--lcars-tan, #cc9966); font-weight: bold; width: 20px; text-align: center;">1M</span>
                        <span>= 1 Momentum to leave hex</span>
                    </div>
                </div>
            </div>
        `;
        container.innerHTML = legendHtml;
    }
};

// Export for use in templates
if (typeof window !== 'undefined') {
    window.HexMap = HexMap;
}
