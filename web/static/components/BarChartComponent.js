export default {
  template: `
    <div style="width:1000px; height:500px;">
        <div class="d-flex">
            <div class="input-group bg-dark">

                <select @change="renderChart" v-model="currentData" class="bg-secondary form-select-sm">
                    <option class="bg-secondary" v-for="(item, index) in results" :value="item" :key="index">
                        {{ item.user }}
                    </option>
                </select>
                <div class="btn-group-sm">
                    <button @click="changeInterval('Daily')" type="button" class="btn btn-secondary" 
                        v-bind:class="{disabled: curentInterval=='Daily'}">День
                    </button>
                    <button @click="changeInterval('Weekly')" type="button" class="btn btn-secondary" 
                        v-bind:class="{disabled: curentInterval=='Weekly'}">Неделя
                    </button>
                    <button @click="changeInterval('Monthly')" type="button" class="btn btn-secondary" 
                        v-bind:class="{disabled: curentInterval=='Monthly'}">Месяц
                    </button>
                </div>
            </div>

        </div>
      <canvas id="myChart" ></canvas>
    </div>
  `,
  data () {
    return {
    chart:null,
    limitAutoUpdate:10,
    curentInterval:'Daily', //Daily, Weekly, Monthly 
    intervals:[],
    results:[],
    currentData:{user:'Все', countSubmit:{succes:[], failure:[], failure_rmc:[]}},
  }}
  ,

  methods:{
    renderChart(){
        if (this.chart) this.chart.reset();
        this.chart = new Chart(this.$el.querySelector('#myChart'), {
                type: 'bar',
                data: {
                    labels: this.intervals,
                    datasets: [
                        {
                        label: 'Успешно',
                        backgroundColor: "#2E8B57",
                        data: this.currentData.countSubmit.succes,
                    }, 

                    {
                        label: 'Ошибка РМЦ',
                        backgroundColor: "#c7ba07ff",
                        data: this.currentData.countSubmit.failure_rmc,
                    },

                    {
                        label: 'Ошибка',
                        backgroundColor: "#CD5C5C",
                        data: this.currentData.countSubmit.failure,
                    },
                  
                  ],
                },
                options: {
                    plugins: {
                        title: {
                            display: true,
                            text: 'Количество отправок',
                            align: 'start',
                            color:"#2E8B57"
                        },

                    },
                    scales: {
                        xAxes: [{
                            stacked: true,

                        }],
                        yAxes: [{
                            stacked: true,
                            ticks: {
                              beginAtZero: true,
                              min:0,
                                  },
                        }]
                    }
                }
        });
    },

    async updateChart(){
        await this.getState(this.curentInterval);
        if (this.limitAutoUpdate<=0) {
            this.renderChart();
            this.limitAutoUpdate=10;
            }
        else{
          this.chart.data.datasets[0].data = this.currentData.countSubmit.succes;
          this.chart.data.datasets[1].data = this.currentData.countSubmit.failure_rmc;
          this.chart.data.datasets[2].data = this.currentData.countSubmit.failure;

          this.chart.update();
          this.limitAutoUpdate=this.limitAutoUpdate-1;
        }
    },

    async changeInterval(interval){
        if (this.curentInterval==interval) return;
        const rest = await this.getState(interval);
        const updated_data = this.results.find(result => result.user === this.currentData.user);
        this.currentData = updated_data;
        this.curentInterval = interval;
        this.renderChart();
        this.limitAutoUpdate = 10;
    },

//------периодическое получение статуса текущего приложения--------------------
    updateState() {
      console.log('Обновление запущено')
      var thisComponent = this;
      this.update=window.setInterval(function () {
        //обновить данные
        thisComponent.updateChart();}, 10000);//интервал запроса статуса мс
   },
//------остановка обновлений--------------------
   stopUpdate() {
      if (this.update) {
        window.clearInterval(this.update)
      }
   },

    async getState(interval) {
      try {
        // Выполняем GET-запрос
        const response = await fetch(window.location.pathname.replace('/', '')+'/gethistory?period='+interval);

        // Проверяем статус ответа
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Парсим JSON ответ
        const resp_json = await response.json();
        this.intervals = resp_json.intervals;
        this.results = resp_json.results;
        return true;
      } catch (err) {
        console.log(err.message || 'Произошла ошибка при запросе');
        console.error('Ошибка запроса:', err);
        return false;
      } 
    },


  },

  mounted() {
    console.log('mounted BarChartComponent');
    this.changeInterval('Daily')
    this.getState('Daily');
    this.renderChart();
		this.updateState();

  },

    //------вызов функции перед выходом-----------
  beforeDestroy () {
    this.stopUpdate();
  }


  }
