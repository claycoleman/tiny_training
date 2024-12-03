/* ----------------------------------------------------------------------
 * Project: TinyEngine
 * Title:   lcd.cpp
 *
 * Reference papers:
 *  - MCUNet: Tiny Deep Learning on IoT Device, NeurIPS 2020
 *  - MCUNetV2: Memory-Efficient Patch-based Inference for Tiny Deep Learning, NeurIPS 2021
 *  - MCUNetV3: On-Device Training Under 256KB Memory, NeurIPS 2022
 * Contact authors:
 *  - Wei-Ming Chen, wmchen@mit.edu
 *  - Wei-Chen Wang, wweichen@mit.edu
 *  - Ji Lin, jilin@mit.edu
 *  - Ligeng Zhu, ligeng@mit.edu
 *  - Song Han, songhan@mit.edu
 *
 * Target ISA:  ARMv7E-M
 * -------------------------------------------------------------------- */

#include "lcd.h"
#include <cstring>
#include "stm32746g_discovery.h"
#include "stm32746g_discovery_lcd.h"
#include "stm32f7xx_hal.h"
#include "OUTPUT_CH.h"

#define TRANS 128

void loadRGB565LCD(uint32_t x, uint32_t y, uint32_t width, uint32_t height,
                   uint16_t *src, uint8_t resize) {
  for (int i = 0; i < height; i++) {
    for (int j = 0; j < width; j++) {

      uint16_t color = src[i * width + j];

      for (int ti = 0; ti < resize; ti++) {
        for (int tj = 0; tj < resize; tj++) {
          BSP_LCD_DrawPixel(x + j * resize + tj, y + i * resize + ti, color);
        }
      }
    }
  }
}

void drawRedBackground(int x1, int x2, int y1, int y2) {
  uint16_t red = 63488;

  for (int i = x1 - 1; i < x2; i++)
    for (int j = y1 - 1; j < y2; j++) {
      BSP_LCD_DrawPixel(i, j, red);
    }
}

void drawGreenBackground(int x1, int x2, int y1, int y2) {
  uint16_t green = 2016;

  for (int i = x1 - 1; i < x2; i++)
    for (int j = y1 - 1; j < y2; j++) {
      BSP_LCD_DrawPixel(i, j, green);
    }
}

void drawBlueBackground(int x1, int x2, int y1, int y2) {
  uint16_t blue = 2016 + 63488;

  for (int i = x1 - 1; i < x2; i++)
    for (int j = y1 - 1; j < y2; j++) {
      BSP_LCD_DrawPixel(i, j, blue);
    }
}

void drawBlackBackground(int x1, int x2, int y1, int y2) {
  uint16_t black = 0;

  for (int i = x1 - 1; i < x2; i++)
    for (int j = y1 - 1; j < y2; j++) {
      BSP_LCD_DrawPixel(i, j, black);
    }
}

void displaystring(char *buf, int x, int y) {
  BSP_LCD_DisplayStringAt(x, y, buf, LEFT_MODE);
}

void displayMultilineText(const char* strings[], int numLines, int x, int y, int lineSpacing = 20) {
  // TODO this is inefficient, we should have our lines be 12 chars max each
  static char padded_line[20];  // Make sure this is long enough for your max width
  for (int i = 0; i < numLines; i++) {
    // Fill with spaces to clear any previous text
    sprintf(padded_line, "%-12s", strings[i]); 
    BSP_LCD_DisplayStringAt(x, y + (i * lineSpacing), padded_line, LEFT_MODE);
  }
}


void displayMs(float ms) {
  if (ms != 0) {
    BSP_LCD_SetTextColor(LCD_COLOR_BLUE);
    volatile float rate = 1000 / ms;
    volatile int decimal = (int)rate;
    volatile int floating = (int)((rate - (float)decimal) * 1000);
    char buf[20];
    sprintf(buf, "  fps:%d.%03d ", decimal, floating);
    BSP_LCD_DisplayStringAt(273, 205, buf, LEFT_MODE);
  }
}

void displayTrainingResponse(int pred, int label) {
  // we print at most 8 lines for training response
  // Prediction or Ground Truth
  // pred_label or true_label line 1
  // pred_label or true_label line 2 (if it's longer than 12 characters)
  // pred or label
  const char* lines[8];
  int numLines = 0;

  // Prepare prediction lines
  lines[numLines++] = "Prediction:";
  
  // Set backgrounds and color as before
  if (pred == label) {
    drawGreenBackground(270, 480, 40, 100);
    drawGreenBackground(270, 480, 125, 180);
    drawGreenBackground(270, 480, 205, 250);
  } else {
    drawRedBackground(270, 480, 40, 100);
    drawRedBackground(270, 480, 125, 180);
    drawRedBackground(270, 480, 205, 250);
  }
  BSP_LCD_SetTextColor(LCD_COLOR_RED);
  
  const char *pred_label = OUTPUT_LABELS[pred];
  const char *true_label = OUTPUT_LABELS[label];
  
  if (strlen(pred_label) > 12) {
    static char first_line[20];
    strncpy(first_line, pred_label, 12);
    first_line[12] = '\0';
    lines[numLines++] = first_line;
    
    static char second_line[20];
    sprintf(second_line, "%s", &pred_label[12]);
    lines[numLines++] = second_line;
  } else {
    lines[numLines++] = pred_label;
  }

  static char pred_class_line[20];
  sprintf(pred_class_line, "  class %d  ", pred);
  lines[numLines++] = pred_class_line;
  
  // Prepare ground truth lines
  lines[numLines++] = "True Label:";
  if (strlen(true_label) > 12) {
    static char first_line[20];
    strncpy(first_line, true_label, 12);
    first_line[12] = '\0';
    lines[numLines++] = first_line;
    
    static char second_line[20];
    sprintf(second_line, "%s", &true_label[12]);
    lines[numLines++] = second_line;
  } else {
    lines[numLines++] = true_label;
  }

  static char true_class_line[20];
  sprintf(true_class_line, "  class %d  ", label);
  lines[numLines++] = true_class_line;
  
  displayMultilineText(lines, numLines, 273, 60);
}

void displayInferenceResponse(int pred) {
  // we print at most 4 lines for inference response
  // Prediction:
  // pred_label line 1
  // pred_label line 2 (if it's longer than 12 characters)
  // class X
  const char* lines[4];
  int numLines = 0;
  
  const char *output_label = OUTPUT_LABELS[pred];
  
  drawBlackBackground(270, 480, 40, 100);
  drawBlackBackground(270, 480, 125, 180);
  drawBlackBackground(270, 480, 205, 250);
  BSP_LCD_SetTextColor(LCD_COLOR_RED);
  
  lines[numLines++] = "Prediction:";
  
  if (strlen(output_label) > 12) {
    static char first_line[20];
    strncpy(first_line, output_label, 12);
    first_line[12] = '\0';
    lines[numLines++] = first_line;
    
    static char second_line[20];
    sprintf(second_line, "%s", &output_label[12]);
    lines[numLines++] = second_line;
  } else {
    lines[numLines++] = output_label;
  }
  
  static char class_line[20];
  sprintf(class_line, "  class %d  ", pred);
  lines[numLines++] = class_line;
  displayMultilineText(lines, numLines, 273, 80);
}

void displayTrainingReady() {
  // wipe out all text below the training ready text
  drawBlackBackground(270, 480, 40, 250);
}

void lcdsetup() {
  RCC_PeriphCLKInitTypeDef PeriphClkInitStruct;

  PeriphClkInitStruct.PeriphClockSelection = RCC_PERIPHCLK_LTDC;
  PeriphClkInitStruct.PLLSAI.PLLSAIN = 192;
  PeriphClkInitStruct.PLLSAI.PLLSAIR = 5;
  PeriphClkInitStruct.PLLSAIDivR = RCC_PLLSAIDIVR_4;
  HAL_RCCEx_PeriphCLKConfig(&PeriphClkInitStruct);

  BSP_LCD_Init();

  BSP_LCD_LayerRgb565Init(0, LCD_FB_START_ADDRESS);
  BSP_LCD_LayerRgb565Init(1, LCD_FB_START_ADDRESS +
                                 (BSP_LCD_GetXSize() * BSP_LCD_GetYSize() * 4));

  BSP_LCD_DisplayOn();

  BSP_LCD_SelectLayer(0);

  BSP_LCD_Clear(LCD_COLOR_BLACK);

  BSP_LCD_SelectLayer(1);

  BSP_LCD_Clear(LCD_COLOR_BLACK);

  BSP_LCD_SetTransparency(0, 0);
  BSP_LCD_SetTransparency(1, 100);

  BSP_LCD_SetTextColor(LCD_COLOR_BLUE);
}
