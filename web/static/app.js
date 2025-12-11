const { createApp } = Vue;

// Импортируем компоненты
import SearchForm from './components/SearchForm.js';
import BarChartComponent from './components/BarChartComponent.js';
import GasCardsComponent from './components/GasCardsComponent.js';

// Создаём корневой компонент
const App = {
  components: {
    // Регистрируем компоненты локально
    SearchForm,
    BarChartComponent,
    GasCardsComponent
  }

};

// Монтируем приложение
createApp(App).mount('#app');
