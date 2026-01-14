<template>
  <div class="restrict-orientation">
    <img src="@/assets/runner.png" alt="Runner Icon" class="runner-icon" />
    <div class="title">Rotate Device</div>
    <div class="content">
      This site is best viewed in landscape mode.
    </div>
  </div>
</template>

<script>
export default {
  name: 'RestrictOrientation',
};
</script>

<style scoped>
.restrict-orientation {
  display: none;
}

@media screen and (max-width: 768px) and (orientation: portrait) {
  .restrict-orientation {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;

    height: 100vh;
    width: 100vw;
    position: fixed;
    top: 0;
    left: 0;
    z-index: 9999;
    background: #ffffff;
    padding: 16px;
    text-align: center;
    transition: all 0.3s ease;
  }
}

/* Runner icon sits above the title */
.runner-icon {
  width: 60px;      /* adjust as needed */
  height: 60px;     /* adjust as needed */
  margin-bottom: 16px; /* space between icon and title */
}

.title {
  font-family: sans-serif;
  font-size: 1.5rem;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.content {
  font-size: 1rem;
}
</style>
