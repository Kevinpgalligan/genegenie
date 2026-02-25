(function() {
    'use strict';

    var CELL = 20;
    var LABEL_W = 180;
    var HEADER_H = 110;
    var GEN_GAP = 12;
    var GEN_LABEL_W = 40;

    var COLORS = {
        parentMale:   '#2c5aa0',
        parentFemale: '#a02c5a',
        childMale:    '#7ba3d4',
        childFemale:  '#d47ba3',
        parentOther:  '#666666',
        childOther:   '#aaaaaa',
        gridLine:     '#ddd',
        genBands:     ['#f3f3fa', '#faf3f3'],
        hoverRow:     'rgba(255, 200, 0, 0.25)',
        hoverCol:     'rgba(255, 200, 0, 0.25)',
        text:         '#333',
        genText:      '#888',
        genSep:       '#bbb',
        bg:           '#fff'
    };

    // ── Data processing ──────────────────────────────────────────────

    function processData(data) {
        var peopleById = new Map();
        data.people.forEach(function(p) { peopleById.set(p.id, p); });

        // Group by generation
        var genMap = new Map();
        data.people.forEach(function(p) {
            if (!genMap.has(p.generation)) genMap.set(p.generation, []);
            genMap.get(p.generation).push(p);
        });
        var genNumbers = Array.from(genMap.keys()).sort(function(a, b) { return a - b; });

        // Assign generation-level to each family (= min parent generation)
        var families = data.families.map(function(fam) {
            var pGens = fam.parents
                .filter(function(id) { return id && peopleById.has(id); })
                .map(function(id) { return peopleById.get(id).generation; });
            var cGens = fam.children
                .filter(function(id) { return peopleById.has(id); })
                .map(function(id) { return peopleById.get(id).generation; });
            var gl = pGens.length > 0
                ? Math.min.apply(null, pGens)
                : (cGens.length > 0 ? Math.min.apply(null, cGens) - 1 : 0);
            return { id: fam.id, parents: fam.parents, children: fam.children, genLevel: gl };
        });
        families.sort(function(a, b) { return a.genLevel - b.genLevel; });

        // Person → index of family they are a child of
        var childOfFam = new Map();
        families.forEach(function(fam, idx) {
            fam.children.forEach(function(cid) {
                if (!childOfFam.has(cid)) childOfFam.set(cid, idx);
            });
        });

        // Person → index of first family they parent
        var parentOfFam = new Map();
        families.forEach(function(fam, idx) {
            fam.parents.forEach(function(pid) {
                if (pid && !parentOfFam.has(pid)) parentOfFam.set(pid, idx);
            });
        });

        // Order people within each generation by family adjacency
        var orderedPeople = [];
        genNumbers.forEach(function(gen) {
            var peeps = genMap.get(gen).slice();
            peeps.sort(function(a, b) {
                var aC = childOfFam.has(a.id) ? childOfFam.get(a.id) : 99999;
                var bC = childOfFam.has(b.id) ? childOfFam.get(b.id) : 99999;
                if (aC !== bC) return aC - bC;
                var aP = parentOfFam.has(a.id) ? parentOfFam.get(a.id) : 99999;
                var bP = parentOfFam.has(b.id) ? parentOfFam.get(b.id) : 99999;
                return aP - bP;
            });
            orderedPeople.push.apply(orderedPeople, peeps);
        });

        // Person → row index
        var personRow = new Map();
        orderedPeople.forEach(function(p, i) { personRow.set(p.id, i); });

        // Refine family column order using person row positions
        families.sort(function(a, b) {
            if (a.genLevel !== b.genLevel) return a.genLevel - b.genLevel;
            var aRows = a.parents.filter(function(id) { return id && personRow.has(id); })
                                 .map(function(id) { return personRow.get(id); });
            var bRows = b.parents.filter(function(id) { return id && personRow.has(id); })
                                 .map(function(id) { return personRow.get(id); });
            var aMin = aRows.length > 0 ? Math.min.apply(null, aRows) : 99999;
            var bMin = bRows.length > 0 ? Math.min.apply(null, bRows) : 99999;
            return aMin - bMin;
        });

        // Row Y-positions (with generation gaps)
        var rowY = [];
        var genBounds = [];   // { y, gen }
        var y = 0;
        var prevGen = null;
        orderedPeople.forEach(function(p) {
            if (prevGen !== null && p.generation !== prevGen) {
                y += GEN_GAP;
                genBounds.push({ y: y, gen: p.generation });
            } else if (prevGen === null) {
                genBounds.push({ y: 0, gen: p.generation });
            }
            rowY.push(y);
            y += CELL;
            prevGen = p.generation;
        });
        var matrixHeight = y;

        // Generation ranges (for band drawing)
        var genRanges = [];
        genBounds.forEach(function(gb, i) {
            var startY = gb.y;
            var endY = (i + 1 < genBounds.length)
                ? genBounds[i + 1].y - GEN_GAP
                : matrixHeight;
            genRanges.push({ gen: gb.gen, startY: startY, endY: endY });
        });

        // Build filled-cell list
        var cells = [];
        families.forEach(function(fam, colIdx) {
            fam.parents.forEach(function(pid) {
                if (pid && personRow.has(pid)) {
                    cells.push({
                        row: personRow.get(pid), col: colIdx,
                        isParent: true, gender: peopleById.get(pid).gender
                    });
                }
            });
            fam.children.forEach(function(cid) {
                if (personRow.has(cid)) {
                    cells.push({
                        row: personRow.get(cid), col: colIdx,
                        isParent: false, gender: peopleById.get(cid).gender
                    });
                }
            });
        });

        return {
            orderedPeople: orderedPeople,
            families: families,
            cells: cells,
            rowY: rowY,
            genBounds: genBounds,
            genRanges: genRanges,
            personRow: personRow,
            peopleById: peopleById,
            numRows: orderedPeople.length,
            numCols: families.length,
            matrixHeight: matrixHeight,
            matrixWidth: families.length * CELL
        };
    }

    // ── Colour helpers ───────────────────────────────────────────────

    function cellColor(isParent, gender) {
        if (isParent) {
            if (gender === 'M') return COLORS.parentMale;
            if (gender === 'F') return COLORS.parentFemale;
            return COLORS.parentOther;
        }
        if (gender === 'M') return COLORS.childMale;
        if (gender === 'F') return COLORS.childFemale;
        return COLORS.childOther;
    }

    // ── Main entry point ─────────────────────────────────────────────

    window.renderQuilt = function(canvasEl, data) {
        var proc = processData(data);
        var ctx = canvasEl.getContext('2d');
        var transform = d3.zoomIdentity;
        var hoverRow = -1, hoverCol = -1;

        // Tooltip
        var tip = document.createElement('div');
        tip.style.cssText =
            'position:fixed;padding:6px 10px;background:#333;color:#fff;' +
            'border-radius:4px;font:12px Helvetica,sans-serif;' +
            'pointer-events:none;display:none;z-index:100;white-space:pre-line';
        document.body.appendChild(tip);

        // ── Resize ───────────────────────────────────────────────────

        function resize() {
            var rect = canvasEl.parentElement.getBoundingClientRect();
            var dpr = window.devicePixelRatio || 1;
            canvasEl.width  = rect.width  * dpr;
            canvasEl.height = rect.height * dpr;
            canvasEl.style.width  = rect.width  + 'px';
            canvasEl.style.height = rect.height + 'px';
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            draw();
        }

        // ── Draw ─────────────────────────────────────────────────────

        function draw() {
            var w = canvasEl.width  / (window.devicePixelRatio || 1);
            var h = canvasEl.height / (window.devicePixelRatio || 1);

            ctx.save();
            ctx.clearRect(0, 0, w, h);
            ctx.translate(transform.x, transform.y);
            ctx.scale(transform.k, transform.k);

            // Generation bands
            proc.genRanges.forEach(function(gr, i) {
                ctx.fillStyle = COLORS.genBands[i % 2];
                ctx.fillRect(LABEL_W, HEADER_H + gr.startY,
                             proc.matrixWidth, gr.endY - gr.startY);
            });

            // Generation separator lines (in the gaps)
            ctx.strokeStyle = COLORS.genSep;
            ctx.lineWidth = 0.5;
            ctx.setLineDash([4, 3]);
            proc.genBounds.forEach(function(gb, i) {
                if (i === 0) return;
                var sepY = HEADER_H + gb.y - GEN_GAP / 2;
                ctx.beginPath();
                ctx.moveTo(GEN_LABEL_W, sepY);
                ctx.lineTo(LABEL_W + proc.matrixWidth, sepY);
                ctx.stroke();
            });
            ctx.setLineDash([]);

            // Hover highlights
            if (hoverRow >= 0) {
                ctx.fillStyle = COLORS.hoverRow;
                ctx.fillRect(0, HEADER_H + proc.rowY[hoverRow],
                             LABEL_W + proc.matrixWidth, CELL);
            }
            if (hoverCol >= 0) {
                ctx.fillStyle = COLORS.hoverCol;
                ctx.fillRect(LABEL_W + hoverCol * CELL, HEADER_H,
                             CELL, proc.matrixHeight);
            }

            // Grid lines
            ctx.strokeStyle = COLORS.gridLine;
            ctx.lineWidth = 0.5;
            proc.genRanges.forEach(function(gr) {
                for (var gy = gr.startY; gy <= gr.endY; gy += CELL) {
                    ctx.beginPath();
                    ctx.moveTo(LABEL_W, HEADER_H + gy);
                    ctx.lineTo(LABEL_W + proc.matrixWidth, HEADER_H + gy);
                    ctx.stroke();
                }
            });
            for (var j = 0; j <= proc.numCols; j++) {
                var x = LABEL_W + j * CELL;
                ctx.beginPath();
                ctx.moveTo(x, HEADER_H);
                ctx.lineTo(x, HEADER_H + proc.matrixHeight);
                ctx.stroke();
            }

            // Filled cells
            var pad = 1;
            proc.cells.forEach(function(c) {
                var cx = LABEL_W + c.col * CELL;
                var cy = HEADER_H + proc.rowY[c.row];
                ctx.fillStyle = cellColor(c.isParent, c.gender);
                if (c.isParent) {
                    // Parents: filled rectangle
                    ctx.fillRect(cx + pad, cy + pad, CELL - 2 * pad, CELL - 2 * pad);
                } else {
                    // Children: filled circle
                    var r = (CELL - 2 * pad) / 2;
                    ctx.beginPath();
                    ctx.arc(cx + CELL / 2, cy + CELL / 2, r, 0, 2 * Math.PI);
                    ctx.fill();
                }
            });

            // Person name labels (left side)
            ctx.font = '11px Helvetica, Arial, sans-serif';
            ctx.fillStyle = COLORS.text;
            ctx.textAlign = 'right';
            ctx.textBaseline = 'middle';
            proc.orderedPeople.forEach(function(p, i) {
                var ly = HEADER_H + proc.rowY[i] + CELL / 2;
                ctx.fillText(p.name, LABEL_W - 5, ly);
            });

            // Generation labels (far left)
            ctx.font = 'bold 11px Helvetica, Arial, sans-serif';
            ctx.fillStyle = COLORS.genText;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            proc.genRanges.forEach(function(gr) {
                var midY = HEADER_H + (gr.startY + gr.endY) / 2;
                ctx.fillText('G' + gr.gen, GEN_LABEL_W / 2, midY);
            });

            // Family column labels (top, angled)
            ctx.save();
            ctx.font = '10px Helvetica, Arial, sans-serif';
            ctx.fillStyle = COLORS.text;
            ctx.textAlign = 'left';
            ctx.textBaseline = 'bottom';
            proc.families.forEach(function(fam, fi) {
                var fx = LABEL_W + fi * CELL + CELL / 2;
                var fy = HEADER_H - 4;
                ctx.save();
                ctx.translate(fx, fy);
                ctx.rotate(-Math.PI / 3);
                var label = fam.parents
                    .filter(function(id) { return id && proc.peopleById.has(id); })
                    .map(function(id) {
                        var n = proc.peopleById.get(id).name;
                        return n.length > 12 ? n.slice(0, 11) + '\u2026' : n;
                    })
                    .join(' & ') || fam.id;
                ctx.fillText(label, 0, 0);
                ctx.restore();
            });
            ctx.restore();

            ctx.restore(); // pop zoom transform
        }

        // ── Zoom ─────────────────────────────────────────────────────

        var zoom = d3.zoom()
            .scaleExtent([0.15, 6])
            .on('zoom', function(event) {
                transform = event.transform;
                draw();
            });
        d3.select(canvasEl).call(zoom);

        // ── Hover ────────────────────────────────────────────────────

        canvasEl.addEventListener('mousemove', function(event) {
            var rect = canvasEl.getBoundingClientRect();
            var mx = event.clientX - rect.left;
            var my = event.clientY - rect.top;
            var dx = (mx - transform.x) / transform.k;
            var dy = (my - transform.y) / transform.k;
            var matX = dx - LABEL_W;
            var matY = dy - HEADER_H;

            var newRow = -1, newCol = -1;

            if (matX >= 0 && matX < proc.matrixWidth && matY >= 0) {
                newCol = Math.floor(matX / CELL);
                if (newCol >= proc.numCols) newCol = -1;
                for (var i = 0; i < proc.numRows; i++) {
                    if (matY >= proc.rowY[i] && matY < proc.rowY[i] + CELL) {
                        newRow = i;
                        break;
                    }
                }
            }

            if (newRow !== hoverRow || newCol !== hoverCol) {
                hoverRow = newRow;
                hoverCol = newCol;
                draw();
            }

            if (newRow >= 0 || newCol >= 0) {
                var parts = [];
                if (newRow >= 0) {
                    var person = proc.orderedPeople[newRow];
                    parts.push(person.name + (person.birthYear ? ' (b. ' + person.birthYear + ')' : ''));
                }
                if (newCol >= 0) {
                    var fam = proc.families[newCol];
                    var pNames = fam.parents
                        .filter(function(id) { return id && proc.peopleById.has(id); })
                        .map(function(id) { return proc.peopleById.get(id).name; });
                    parts.push('Family: ' + (pNames.join(' & ') || fam.id));
                    if (newRow >= 0) {
                        var pid = proc.orderedPeople[newRow].id;
                        var role = fam.parents.indexOf(pid) >= 0 ? 'Parent'
                                 : fam.children.indexOf(pid) >= 0 ? 'Child'
                                 : '';
                        if (role) parts.push('Role: ' + role);
                    }
                }
                tip.style.display = 'block';
                tip.style.left = (event.clientX + 14) + 'px';
                tip.style.top  = (event.clientY + 14) + 'px';
                tip.textContent = parts.join('\n');
            } else {
                tip.style.display = 'none';
            }
        });

        canvasEl.addEventListener('mouseleave', function() {
            hoverRow = -1;
            hoverCol = -1;
            tip.style.display = 'none';
            draw();
        });

        // ── Init ─────────────────────────────────────────────────────

        window.addEventListener('resize', resize);
        resize();

        // Fit the chart into view initially
        var totalW = LABEL_W + proc.matrixWidth + 40;
        var totalH = HEADER_H + proc.matrixHeight + 40;
        var vw = canvasEl.parentElement.getBoundingClientRect().width;
        var vh = canvasEl.parentElement.getBoundingClientRect().height;
        var scale = Math.min(vw / totalW, vh / totalH, 1);
        var initTransform = d3.zoomIdentity
            .translate(10, 10)
            .scale(scale);
        d3.select(canvasEl).call(zoom.transform, initTransform);
    };
})();
