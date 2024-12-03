/* ----------------------------------------------------------------------
 * Project: Tiny Training Engine, MCUNetV3
 * Title:   main.cpp
 *
 * Reference papers:
 *  - MCUNet: Tiny Deep Learning on IoT Device, NeurIPS 2020
 *  - MCUNetV2: Memory-Efficient Patch-based Inference for Tiny Deep Learning, NeurIPS 2021
 *  - MCUNetV3: On-Device Training Under 256KB Memory, NeurIPS 2022
 * Contact authors:
 *  - Wei-Chen Wang, wweichen@mit.edu
 *  - Wei-Ming Chen, wmchen@mit.edu
 *  - Ji Lin, jilin@mit.edu
 *  - Ligeng Zhu, ligeng@mit.edu
 *  - Song Han, songhan@mit.edu
 *  - Chuang Gan, ganchuang@csail.mit.edu
 *
 * Target ISA:  ARMv7E-M
 * -------------------------------------------------------------------- */

#include "main.h"
#include "camera.h"
#include "lcd.h"
#include "profile.h"
#include "stdio.h"
#include "string.h"
#include "testing_data/golden_data.h"
#include "testing_data/images.h"
#include "OUTPUT_CH.h"

extern "C" {
#include "genNN.h"
#include "tinyengine_function.h"
}
#define SHOWIMG

#include "stm32746g_discovery.h"

static void SystemClock_Config(void);
static void Error_Handler(void);
static void CPU_CACHE_Enable(void);
static void MX_GPIO_Init(void);

#define IMAGE_H 80
#define IMAGE_W 80
#define INPUT_CH 160
#define IMAGES 6

void SystemClock_Config(void);
void StartDefaultTask(void const *argument);

signed char out_int[OUTPUT_CH];

float labels[] = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
void train(int cls) {
  // TODO find a way to throw if cls is not in the range of 0 to OUTPUT_CH - 1
  char cbuf[20];
  // Current model architecture has 10 output classes, and isn't dependent on OUTPUT_CH
  for (int i = 0; i < 10; i++) {
    if (i == cls) {
      labels[i] = 1.0f;
    } else
      labels[i] = 0.0f;
  }
  // this line actually runs backprop on the loaded image
  invoke(labels);
}

void invoke_new_weights_givenimg(signed char *out_int8) {
  invoke_inf();
  signed char *output = (signed char *)getOutput();
  for (int i = 0; i < OUTPUT_CH; i++)
    out_int8[i] = output[i];
}

#define BUTTON1_Pin GPIO_PIN_0
#define BUTTON1_GPIO_Port GPIOA
#define BUTTON2_Pin GPIO_PIN_10
#define BUTTON2_GPIO_Port GPIOF

#define RES_W 128
#define RES_H 120

const int scale_factor = 1;
uint16_t *RGBbuf;
#define ENABLE_TRAIN

void readCameraInputsIntoMemory(signed char *input, uint16_t *RGBbuf) {
  ReadCapture();
  StartCapture();
  DecodeandProcessAndRGB(RES_W, RES_H, input, RGBbuf, scale_factor);
}

void displayCameraInputOnLCD(signed char *input, uint16_t *RGBbuf) {
  // DecodeandProcessAndRGB will write colors to the RGBbuf if scale_factor == 1
  // we manually write 565 colors to the RGBbuf if scale_factor != 1
  if (scale_factor != 1) {
    // THIS CODE IS UNTESTED SINCE SCALE FACTOR IS SET TO 1
    // if we have more width than height, we need to zero out the extra width
    if (RES_W > RES_H) {
      for (int i = 0; i < RES_W * (RES_W - RES_H) * 3; i++) {
        input[RES_H * RES_W * 3 + i] = -128;
      }
    } else if (RES_H > RES_W) {
      for (int i = 0; i < RES_H * (RES_H - RES_W) * 3; i++) {
        input[RES_W * RES_H * 3 + i] = -128;
      }
    }
    // input is now a 128x128x3 array of signed chars
    // convert our input to rgb565
    for (int y = 0; y < RES_H; y++) {
      for (int x = 0; x < RES_W; x++) {
        // cast to int32_t to avoid overflow
        uint8_t red = (int32_t)input[(RES_W * y + x) * 3] + 128;
        uint8_t green = (int32_t)input[(RES_W * y + x) * 3 + 1] + 128;
        uint8_t blue = (int32_t)input[(RES_W * y + x) * 3 + 2] + 128;

        // converting rgb888 to rgb565
        uint16_t b = (blue >> 3) & 0x1f;
        uint16_t g = ((green >> 2) & 0x3f) << 5;
        uint16_t r = ((red >> 3) & 0x1f) << 11;

        RGBbuf[RES_W * y + x] = (uint16_t)(r | g | b);
      }
    }
  }
  // displays from (10, 10) to (10 + RES_W, 10 + RES_H).
  loadRGB565LCD(10, 10, RES_W, RES_H, RGBbuf, 2);
}

const char DEFAULT_CMD_CHAR = 'c';

int main(void) {
  char buf[150];
  char showbuf[150];

  CPU_CACHE_Enable();
  HAL_Init();

  SystemClock_Config();

  MX_GPIO_Init();

  BSP_PB_Init(BUTTON_KEY, BUTTON_MODE_GPIO);

  lcdsetup();

  int camErr = initCamera();

  uint32_t start, end, starti, endi;
  StartCapture();
  signed char *input = getInput();
  
  // we have space allocated for the display buffer in input, but it's after
  // the rgba 128x128 uint8 image.
  RGBbuf = (uint16_t *)&input[128 * 128 * 4];
  bool training_mode = false;
  bool validation_mode = false;
  bool just_started_training_mode = false;
  while (1) {
    starti = HAL_GetTick();
    readCameraInputsIntoMemory(input, RGBbuf);
    displayCameraInputOnLCD(input, RGBbuf);
    endi = HAL_GetTick();

    uint8_t button0 = BSP_PB_GetState(BUTTON_KEY) == GPIO_PIN_SET;
    uint8_t button1 = !HAL_GPIO_ReadPin(BUTTON1_GPIO_Port, BUTTON1_Pin);
    uint8_t button2 = !HAL_GPIO_ReadPin(BUTTON2_GPIO_Port, BUTTON2_Pin);

    char s[1] = {DEFAULT_CMD_CHAR};
    /**
     * t => training mode
     * i => inference mode
     * 
     * class number => train that class
     */
    receiveChar(s);
    if (s[0] != DEFAULT_CMD_CHAR) {
      char cmdLog[150];
      // KEY COORDINATION LOG
      sprintf(cmdLog, "COMMAND RECEIVED: %c\r\n", s[0]);
      printLog(cmdLog);
    }
    if (s[0] == 't') {
      just_started_training_mode = training_mode != 1;
      training_mode = true;
      printLog("Switching to training mode\r\n");
    } else if (s[0] == 'i') {
      training_mode = false;
      validation_mode = false;
      printLog("Switching to inference mode\r\n");
    } else if (s[0] == 'v') {
      training_mode = false;
      validation_mode = true;
      printLog("Switching to validation mode\r\n");
    }
    
    if (training_mode) {
      if (just_started_training_mode) {
        sprintf(showbuf, "Train Ready");
        displaystring(showbuf, 273, 10);
        displayTrainingReady();
      }
      just_started_training_mode = false;
      bool is_valid_class_number = s[0] >= '0' && s[0] <= '0' + OUTPUT_CH - 1;
      if (is_valid_class_number || button1 || button2) {
        int true_class_from_user_input = 0;
        
        if (is_valid_class_number) {
          true_class_from_user_input = s[0] - '0';
          // assert true_class_from_user_input is now between 0 and OUTPUT_CH - 1
          if (true_class_from_user_input < 0 || true_class_from_user_input >= OUTPUT_CH) {
            char logbuf[150];
            sprintf(logbuf, "Invalid class number %d\r\n", true_class_from_user_input);
            printLog(logbuf);
            continue;
          }
          sprintf(showbuf, "Train cls %d", true_class_from_user_input);
        } else if (button2) {
          true_class_from_user_input = 1;
          sprintf(showbuf, "Train cls 1");
        } else if (button1) {
          true_class_from_user_input = 0;
          sprintf(showbuf, "Train cls 0");
        }

        // log with string interpolation
        char logbuf[150];
        sprintf(logbuf, "Training: Train cls %d\r\n", true_class_from_user_input);
        printLog(logbuf);

        invoke_new_weights_givenimg(out_int);
        int predicted_class = 0;
        // Get max output class
        for (int i = 0; i < OUTPUT_CH; i++) {
          predicted_class = out_int[i] > out_int[predicted_class] ? i : predicted_class;
        }

        displayTrainingResponse(predicted_class, true_class_from_user_input);

        // about to read next frame
        // we train on the latest possible image, one that might not be same as the one displayed...
        readCameraInputsIntoMemory(input, RGBbuf);
        displaystring(showbuf, 273, 10);
        start = HAL_GetTick();
        train(true_class_from_user_input);
        end = HAL_GetTick();
        sprintf(showbuf, "Train done ");
        // KEY COORDINATION LOG
        printLog("TRAINING DONE\r\n");
        displaystring(showbuf, 273, 10);
        displayMs(end - start);

        // TODO: determine if this is the best way to do this
        readCameraInputsIntoMemory(input, RGBbuf);
        // KEY COORDINATION LOG
        printLog("READY FOR NEXT TRAINING\r\n");
      } 
    } else {
      // inference mode or validation mode
      // we run inference on the image loaded at the start of the loop
      start = HAL_GetTick();
      invoke_new_weights_givenimg(out_int);
      // Max predicted label
      int predicted_class = 0;
      for (int i = 0; i < OUTPUT_CH; i++) {
        predicted_class = out_int[i] > out_int[predicted_class] ? i : predicted_class;
      }  
      end = HAL_GetTick();
      if (validation_mode) {
        sprintf(showbuf, " Validation ");
        // output validation mode class
        char logbuf[150];
        // KEY COORDINATION LOG
        sprintf(logbuf, "INFERENCE COMPLETE: %d\r\n", predicted_class);
        printLog(logbuf);
      } else {
        sprintf(showbuf, " Inference ");
      }
      displaystring(showbuf, 273, 10);
      displayInferenceResponse(predicted_class);
      displayMs(end - start);
    }
  }

  while (1) {
  }
}

void SystemClock_Config(void) {
  RCC_ClkInitTypeDef RCC_ClkInitStruct;
  RCC_OscInitTypeDef RCC_OscInitStruct;
  HAL_StatusTypeDef ret = HAL_OK;

  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = 25;
  RCC_OscInitStruct.PLL.PLLN = 432;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 9;

  ret = HAL_RCC_OscConfig(&RCC_OscInitStruct);
  if (ret != HAL_OK) {
    while (1) {
      ;
    }
  }

  ret = HAL_PWREx_EnableOverDrive();
  if (ret != HAL_OK) {
    while (1) {
      ;
    }
  }

  RCC_ClkInitStruct.ClockType = (RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK |
                                 RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2);
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV4;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV2;

  ret = HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_7);
  if (ret != HAL_OK) {
    while (1) {
      ;
    }
  }
}
static void Error_Handler(void) {

  BSP_LED_On(LED1);
  while (1) {
  }
}

static void CPU_CACHE_Enable(void) {

  SCB_EnableICache();

  SCB_EnableDCache();
}

static void MX_GPIO_Init(void) {
  GPIO_InitTypeDef GPIO_InitStruct = {0};

  __HAL_RCC_GPIOE_CLK_ENABLE();
  __HAL_RCC_GPIOG_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOJ_CLK_ENABLE();
  __HAL_RCC_GPIOI_CLK_ENABLE();
  __HAL_RCC_GPIOK_CLK_ENABLE();
  __HAL_RCC_GPIOF_CLK_ENABLE();
  __HAL_RCC_GPIOH_CLK_ENABLE();

  HAL_GPIO_WritePin(OTG_FS_PowerSwitchOn_GPIO_Port, OTG_FS_PowerSwitchOn_Pin,
                    GPIO_PIN_SET);

  HAL_GPIO_WritePin(GPIOI, ARDUINO_D7_Pin | ARDUINO_D8_Pin, GPIO_PIN_RESET);

  HAL_GPIO_WritePin(LCD_BL_CTRL_GPIO_Port, LCD_BL_CTRL_Pin, GPIO_PIN_SET);

  HAL_GPIO_WritePin(LCD_DISP_GPIO_Port, LCD_DISP_Pin, GPIO_PIN_SET);

  HAL_GPIO_WritePin(DCMI_PWR_EN_GPIO_Port, DCMI_PWR_EN_Pin, GPIO_PIN_RESET);

  HAL_GPIO_WritePin(GPIOG, ARDUINO_D4_Pin | ARDUINO_D2_Pin | EXT_RST_Pin,
                    GPIO_PIN_RESET);

  GPIO_InitStruct.Pin = OTG_HS_OverCurrent_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(OTG_HS_OverCurrent_GPIO_Port, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = RMII_TXD1_Pin | RMII_TXD0_Pin | RMII_TX_EN_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.Alternate = GPIO_AF11_ETH;
  HAL_GPIO_Init(GPIOG, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = ULPI_D7_Pin | ULPI_D6_Pin | ULPI_D5_Pin | ULPI_D3_Pin |
                        ULPI_D2_Pin | ULPI_D1_Pin | ULPI_D4_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.Alternate = GPIO_AF10_OTG_HS;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = SPDIF_RX0_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  GPIO_InitStruct.Alternate = GPIO_AF8_SPDIFRX;
  HAL_GPIO_Init(SPDIF_RX0_GPIO_Port, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = OTG_FS_VBUS_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(OTG_FS_VBUS_GPIO_Port, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = Audio_INT_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_EVT_RISING;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(Audio_INT_GPIO_Port, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = OTG_FS_P_Pin | OTG_FS_N_Pin | OTG_FS_ID_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.Alternate = GPIO_AF10_OTG_FS;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = OTG_FS_PowerSwitchOn_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(OTG_FS_PowerSwitchOn_GPIO_Port, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = ARDUINO_D7_Pin | ARDUINO_D8_Pin | LCD_DISP_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOI, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = uSD_Detect_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(uSD_Detect_GPIO_Port, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = LCD_BL_CTRL_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(LCD_BL_CTRL_GPIO_Port, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = OTG_FS_OverCurrent_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(OTG_FS_OverCurrent_GPIO_Port, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = TP3_Pin | NC2_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOH, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = ARDUINO_SCK_D13_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  GPIO_InitStruct.Alternate = GPIO_AF5_SPI2;
  HAL_GPIO_Init(ARDUINO_SCK_D13_GPIO_Port, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = DCMI_PWR_EN_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(DCMI_PWR_EN_GPIO_Port, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = GPIO_PIN_11;
  GPIO_InitStruct.Mode = GPIO_MODE_ANALOG;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOI, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = LCD_INT_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_EVT_RISING;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(LCD_INT_GPIO_Port, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = ULPI_NXT_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.Alternate = GPIO_AF10_OTG_HS;
  HAL_GPIO_Init(ULPI_NXT_GPIO_Port, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = ARDUINO_D4_Pin | ARDUINO_D2_Pin | EXT_RST_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOG, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = ULPI_STP_Pin | ULPI_DIR_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.Alternate = GPIO_AF10_OTG_HS;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = RMII_MDC_Pin | RMII_RXD0_Pin | RMII_RXD1_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.Alternate = GPIO_AF11_ETH;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = RMII_RXER_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(RMII_RXER_GPIO_Port, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = RMII_REF_CLK_Pin | RMII_MDIO_Pin | RMII_CRS_DV_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.Alternate = GPIO_AF11_ETH;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = ULPI_CLK_Pin | ULPI_D0_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.Alternate = GPIO_AF10_OTG_HS;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = ARDUINO_MISO_D12_Pin | ARDUINO_MOSI_PWM_D11_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  GPIO_InitStruct.Alternate = GPIO_AF5_SPI2;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = BUTTON1_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(BUTTON1_GPIO_Port, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = BUTTON2_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(BUTTON2_GPIO_Port, &GPIO_InitStruct);
}

#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line) {

  while (1) {
  }
}
#endif
