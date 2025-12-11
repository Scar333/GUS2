export default {
  template: `
    <div class="row d-flex">
        <div v-for="card in cardsData" class="card text-black shadow  m-3"  style="width:400px"
                
        >
            <div class="card-header" v-bind:class="[{'bg-success': card.status=='Активен'},{'bg-secondary': card.status=='Ожидание'}]">
                <div>
                    <strong>{{card.nameUser}}</strong>
                    <span class="float-right  p-1">{{card.status}}</span>
                </div>

            </div>
            <div class="card-body bg-secondary">
                <div>
                    <span>Проект:</span>
                    <span class="float-right font-weight-bold">{{card.project}}</span>
                </div>
                <div>
                    <span>Текущий реестр:</span>
                    <span class="float-right font-weight-bold">{{card.numRegister}}</span>
                </div>
                <div>
                    <span>Отправлено:</span>
                    <span class="float-right font-weight-bold">{{card.sentToday}}</span>
                </div>
                <div>
                    <span>Последняя отправка:</span>
                    <span class="float-right font-weight-bold">{{card.lastSent}}</span>
                </div>
                <div>
                    <span>В очереди:</span>
                    <span class="float-right font-weight-bold">{{card.packetsInQueue}}</span>
                </div>
                <div>
                    <span>Осталось при текущей скорости:</span>
                    <span class="float-right font-weight-bold">{{card.howLongWait}}</span>
                </div>
            </div>
            <div class="card-footer bg-secondary">
                <button type="button" class="btn btn-primary"
                v-on:click="showModal(card)" 
                v-bind:style="{'display': (card.status!='Активен') ? '' : 'none'}"
                v-bind:class="{'display': (card.status!='Активен') ? '' : 'none'}"
                
                >Запустить подачу</button>
                <button type="button" class="btn btn-dark float-right" style="display:none">Запустить парсинг</button>
            </div>

        </div>
    </div>
    <!-- modal -->
    <div class="modal fade" id="myModal" aria-hidden="false"
    v-bind:class="{show: modal.show}"
    v-bind:style="{'display': (modal.show) ? 'block' : 'none'}"
    >
        <div class="modal-dialog">
            <div class="modal-content">

                <div class="modal-header">
                    <h6 class="modal-title">{{modal.name}}</h6>
                </div>

                <div class="modal-body">
                    <h5>Перед запуском нужно убедиться, что пакеты документов подготовлены!</h5>
                    <div v-if="modal.updating" class="spinner-border text-succes" role="status"></div> 
                    <div v-if="modal.msg">{{modal.msg}}</div> 
                </div>
                
                <div class="modal-footer">
                    <button v-on:click="hideModal()" type="button" class="btn btn-default" data-dismiss="modal">Закрыть</button>
                    <button v-if="!modal.updating" v-on:click="startSubmit(modal.name)" type="button" class="btn btn-primary">Запустить</button>
                </div>
                
            </div>
        </div>
    </div>
<div v-bind:class="[{'modal-backdrop': modal.show},{'show': modal.show}]"></div>
  `,
  data() {
    return { 
        cardsData: [],
    modal:{show:false, name:null, msg:null, updating:false},

    }
  },

methods: {
    showModal(userCard) {
        console.log(userCard);
    if (userCard.status=='Активен'){
        return
    };
      this.modal.name=userCard.nameUser;
      this.modal.show=true;
    },
    hideModal() {
      this.modal.name=null;
      this.modal.msg=null;
      this.modal.show=false;
    },
    async startSubmit(userCard){
      try {
        this.modal.updating = true;
        const response = await fetch(window.location.pathname.replace('/', '')+'/startsubmit?username='+this.modal.name);

        // Проверяем статус ответа
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        this.getState();
        this.hideModal();

      } catch (err) {
        console.log(err.message || 'Произошла ошибка при запросе');
        console.error('Ошибка запроса:', err);
        this.modal.msg = err.message ||'Произошла ошибка при запросе ';
      } finally {
        this.modal.updating = false;
      }

    },

    async getState() {
        //Обновляет инфу по карточкам
      try {
        const response = await fetch(window.location.pathname.replace('/', '')+'/getstate');

        // Проверяем статус ответа
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Парсим JSON ответ
        this.cardsData = await response.json();

      } catch (err) {
        console.log(err.message || 'Произошла ошибка при запросе');
        console.error('Ошибка запроса:', err);
      } finally {
        return
      }
    },

//------периодическое получение статуса текущего приложения--------------------
    updateState() {
      var thisComponent = this;
	  //console.log('showLocaleInfo');
      this.update=window.setInterval(function () {
		thisComponent.getState()

    }, 10000);//интервал запроса статуса мс
   },
//------остановка обновлений--------------------
   stopUpdate() {
      if (this.update) {
        window.clearInterval(this.update)
      }
      if (this.update) {
        window.clearInterval(this.update)
      }
   }


    },
//------получает данные до формирования страницы-----------
  beforeMount() {
    this.getState();
    },

//------вызов функции после формирования страницы-----------
	mounted() {
		this.updateState();

  },

  //------вызов функции перед -----------
  beforeDestroy () {
    this.stopUpdate()
  }

}