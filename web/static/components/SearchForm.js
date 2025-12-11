export default {
  template: `
  <div class="row">
    <div class="col-sm-4">
        <form>
            <div class="form-group ">
                <label class="text-light" for="lawsuitId">Id подачи РМЦ(Lawsuit Id):</label>
                <input v-model="lawsuitId" title="Допускаются только числа" class="form-control" id="lawsuitId">
                <div style="color: red" v-if="isNaN(lawsuitId)">Допускается ввод только чисел</div>
                <template v-if="isUpdating==true">
                    <div class="progress">
                    <div class="progress-bar progress-bar-striped progress-bar-animated"style="width:100%"></div>
                    </div>
                </template>
            </div>
            <div class="btn-group" v-if="isUpdating!=true">
                <button type="submit" class="btn btn-primary"  @click="uploadData">Найти</button>

            </div>
        </form>
    </div>
  </div>

<template v-if="isUpdating!=true && globalError==null">
  <div class="row">
      <div class="col-sm-12">
          <div class="list-group-item list-group-item-action list-group-item-secondary"
                  v-bind:class="[{'list-group-item-success': dbData.state=='Завершено'},
                                  {'list-group-item-danger': dbData.error!=null},
                      ]" data-toggle="tooltip">

              <template v-if="dbData.error==null">
                  <div><b>Id подачи(LawsuitId):</b> {{lawsuitId}}</div>
                  <div><b>ФИО:</b> {{dbData.clientName}}</div>
                  <div><b>Статус:</b> {{dbData.state}}</div>
                  <div><b>Подробности:</b> {{dbData.stateDescription}}</div>
                  <div><b>Номер ГАСП:</b> {{dbData.resultNum}}</div>
              </template>

              <template v-else>
                  <div><b>Не удалось загрузить данные из БД</b></div>
                  <div><b>Причина:</b> {{dbData.error}}</div>
              </template>
          </div>
      </div>
  </div>


</template>

<template v-else-if="isUpdating!=true && globalError!=null">
  <div class="row">
    <div class="col-sm-12">
      <div class="list-group-item list-group-item-action list-group-item-danger">
        <div><b>Нет ответа от сервера</b></div>
        <div><b>Ошибка:</b> {{globalError}}</div>
      </div>
    </div>
  </div>
</template>

  `,
  data() {
    return { 
        globalError:null,
        lawsuitId:null,
        isUpdating: null, 
        dbData: {
            error: null,
            clientName:null, 
            state:null, 
            stateDescription:null,
            resultNum:null,
        },
    }
  },
  methods: {
    resetState() {

      this.globalError = null;
      this.dbData.error = null;
      this.dbData.clientName = null;
      this.dbData.state = null;
      this.dbData.stateDescription = null;
      this.dbData.resultNum = null;
        },
    

    async uploadData() {
      //проверка что lawsuitId введен
      if (!this.lawsuitId) {
        console.log('Не введен id Клиента');
        return;
        };
      //проверка что обновление данных не запущено
      if (this.isUpdating) {
        console.log('Обновление уже запущено');
        return;
        };
      //проверка что lawsuitId число
      if (isNaN(this.lawsuitId)) {
        console.log('Допустим ввод только чисел');
        return;
        };
      
      this.isUpdating = true;
      this.resetState();
      
      const formData = new FormData();
      formData.append('lawsuitId', this.lawsuitId);
      
      try {
        // Замените URL на ваш реальный API endpoint
        const response = await this.uploadToServer(
          '/getresult', 
          formData
        );

        //получаем данные
        this.dbData.error = response.error;
        this.dbData.clientName = response.clientName;
        this.dbData.state = response.state;
        this.dbData.stateDescription = response.stateDescription;
        this.dbData.resultNum = response.resultNum;


      } catch (error) {
        console.error('Update error ==:', error);
        this.globalError = error.message || 'Произошла ошибка при обновлении данных';
      } finally {
        this.isUpdating = false;
      }
    },


    uploadToServer(url, formData) {
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        // Отслеживание прогресса
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            this.progress = Math.round((event.loaded / event.total) * 100);
          }
        });
        
        // Обработка завершения
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            reject(new Error(`Server responded with status ${xhr.status}`));
          }
        });
        
        // Обработка ошибок
        xhr.addEventListener('error', () => {
          reject(new Error('Network error'));
        });
        
        xhr.open('POST', url, true);
        
        // Добавьте здесь заголовки авторизации при необходимости
        // xhr.setRequestHeader('Authorization', 'Bearer your-token');
        
        xhr.send(formData);
      });
    }
    
    },


}