<!-- Copyright 2024 Karlsruhe Institute of Technology
   -
   - Licensed under the Apache License, Version 2.0 (the "License");
   - you may not use this file except in compliance with the License.
   - You may obtain a copy of the License at
   -
   -     http://www.apache.org/licenses/LICENSE-2.0
   -
   - Unless required by applicable law or agreed to in writing, software
   - distributed under the License is distributed on an "AS IS" BASIS,
   - WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   - See the License for the specific language governing permissions and
   - limitations under the License. -->

<script setup>
import {onMounted, onUnmounted, ref, useTemplateRef} from 'vue';

const state = ref('start');
const score = ref(0);
const rank = ref(null);

const dialogRef = useTemplateRef('dialog-ref');
const canvasRef = useTemplateRef('canvas-ref');

let food = null;
let dialog = null;
let context = null;
let gameActive = false;

let count = 0;
let maxScore = 0;
let dx = 0;
let dy = 0;
let keyIndex = 0;

const width = 375;
const height = 375;
const grid = 25;
const initialSegments = 5;

const snake = {
  x: 0,
  y: 0,
  dx: 0,
  dy: 0,
  numSegments: 0,
  segments: [],
};

const ranks = [
  [1, 'S', 'gold'],
  [0.75, 'A', 'lawngreen'],
  [0.3, 'B', 'dodgerblue'],
  [0.1, 'C', 'orchid'],
  [0, 'D', 'tomato'],
];

const keySequence = [38, 38, 40, 40, 37, 39, 37, 39, 66, 65];

function generateFood() {
  const foodBucket = [];

  for (let x = 0; x < width; x += grid) {
    for (let y = 0; y < width; y += grid) {
      if (snake.segments.some((segment) => segment.x === x && segment.y === y)) {
        continue;
      }

      foodBucket.push({x, y});
    }
  }

  if (foodBucket.length === 0) {
    return null;
  }

  const index = Math.floor(Math.random() * foodBucket.length);
  return foodBucket[index];
}

function openGame() {
  gameActive = true;
  dialog = $(dialogRef.value).modal({backdrop: 'static', keyboard: false});
}

function startGame() {
  count = 0;
  score.value = 0;
  dx = 1;
  dy = 0;

  snake.x = Math.floor((width / grid) / 2) * grid;
  snake.y = Math.floor((height / grid) / 2) * grid;
  snake.numSegments = initialSegments;
  snake.segments = [];

  rank.value = ranks[ranks.length - 1];
  state.value = 'play';

  food = generateFood();

  // eslint-disable-next-line no-use-before-define
  window.requestAnimationFrame(gameLoop);
}

function endGame() {
  for (const rank_ of ranks) {
    const threshold = Math.floor(rank_[0] * maxScore);

    if (score.value >= threshold) {
      rank.value = rank_;
      break;
    }
  }

  state.value = 'over';
  context.clearRect(0, 0, width, width);
}

function renderGame() {
  context.clearRect(0, 0, width, width);

  // Draw food.
  context.fillStyle = 'firebrick';
  context.fillRect(food.x, food.y, grid - 1, grid - 1);

  // Draw snake.
  context.fillStyle = '#00695B';

  for (const segment of snake.segments) {
    context.fillRect(segment.x, segment.y, grid - 1, grid - 1);
    context.fillStyle = '#009682';
  }
}

function gameLoop() {
  if (state.value !== 'play') {
    return;
  }

  window.requestAnimationFrame(gameLoop);

  // Game runs at 12 FPS.
  if (++count < 5) {
    return;
  }

  count = 0;

  // Apply direction and move snake.
  snake.dx = dx;
  snake.dy = dy;

  snake.x += snake.dx * grid;
  snake.y += snake.dy * grid;

  // Wrap snake position horizontally.
  if (snake.x < 0) {
    snake.x = width - grid;
  } else if (snake.x >= width) {
    snake.x = 0;
  }

  // Wrap snake position vertically.
  if (snake.y < 0) {
    snake.y = width - grid;
  } else if (snake.y >= width) {
    snake.y = 0;
  }

  // Keep track of where snake has been.
  snake.segments.unshift({x: snake.x, y: snake.y});

  // Remove segments as we move away from them.
  if (snake.segments.length > snake.numSegments) {
    snake.segments.pop();
  }

  renderGame();

  snake.segments.forEach((segment, index) => {
    // Check if snake ate the food.
    if (segment.x === food.x && segment.y === food.y) {
      score.value++;
      snake.numSegments++;

      food = generateFood();

      if (!food) {
        endGame();
        return;
      }

      renderGame();
    }

    // Check collision with all segments after the current one.
    for (let i = index + 1; i < snake.segments.length; i++) {
      if (segment.x === snake.segments[i].x && segment.y === snake.segments[i].y) {
        endGame();
        return;
      }
    }
  });
}

function keydownHandler(e) {
  if (gameActive) {
    e.preventDefault();

    if (state.value === 'play') {
      if (snake.dy === 0) {
        if (e.key === 'ArrowUp') {
          dy = -1;
          dx = 0;
        } else if (e.key === 'ArrowDown') {
          dy = 1;
          dx = 0;
        }
      }

      if (snake.dx === 0) {
        if (e.key === 'ArrowLeft') {
          dx = -1;
          dy = 0;
        } else if (e.key === 'ArrowRight') {
          dx = 1;
          dy = 0;
        }
      }
    } else {
      if (e.key === ' ') {
        startGame();
      }
    }
  } else {
    keyIndex = keySequence[keyIndex] === e.keyCode ? keyIndex + 1 : 0;

    if (keyIndex >= keySequence.length) {
      keyIndex = 0;
      openGame();
    }
  }
}

onMounted(() => {
  context = canvasRef.value.getContext('2d');
  maxScore = ((width / grid) * (width / grid)) - initialSegments;

  document.addEventListener('keydown', keydownHandler);
});

onUnmounted(() => {
  dialog.modal('dispose');
  document.removeEventListener('keydown', keydownHandler);
});
</script>

<template>
  <div ref="dialog-ref" class="modal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header d-flex align-items-center py-2">
          <span class="modal-title">
            <strong>Score:</strong> {{ score }}
          </span>
          <button type="button" class="close" data-dismiss="modal" @click="gameActive = false">
            <i class="fa-solid fa-xmark fa-xs"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="menu d-flex flex-column align-items-center">
            <h5 v-if="state === 'start'">Press [Space Bar]</h5>
            <h4 v-if="state === 'over'" class="font-weight-bold">Game Over</h4>
            <h4 v-if="state === 'over'">
              Rank: <strong class="rank" :style="{'color': rank[2]}">{{ rank[1] }}</strong>
            </h4>
          </div>
          <canvas ref="canvas-ref" :width="width" :height="height" class="border border-primary"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
canvas {
  vertical-align: bottom;
}

.menu {
  left: 50%;
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
}

.modal-dialog {
  max-width: max-content;
}

.rank {
  text-shadow: -1px 0 black, 0 1px black, 1px 0 black, 0 -1px black;
}
</style>
