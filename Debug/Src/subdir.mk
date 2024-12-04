################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (12.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
../Src/JPEGDecoder.cpp \
../Src/camera.cpp \
../Src/camera_i2c.cpp \
../Src/camera_spi.cpp \
../Src/lcd.cpp \
../Src/main.cpp 

S_SRCS += \
../Src/startup_stm32f746xx.s 

C_SRCS += \
../Src/picojpeg.c \
../Src/stm32f7xx_hal_msp.c \
../Src/stm32f7xx_it.c \
../Src/system_stm32f7xx.c 

S_DEPS += \
./Src/startup_stm32f746xx.d 

C_DEPS += \
./Src/picojpeg.d \
./Src/stm32f7xx_hal_msp.d \
./Src/stm32f7xx_it.d \
./Src/system_stm32f7xx.d 

OBJS += \
./Src/JPEGDecoder.o \
./Src/camera.o \
./Src/camera_i2c.o \
./Src/camera_spi.o \
./Src/lcd.o \
./Src/main.o \
./Src/picojpeg.o \
./Src/startup_stm32f746xx.o \
./Src/stm32f7xx_hal_msp.o \
./Src/stm32f7xx_it.o \
./Src/system_stm32f7xx.o 

CPP_DEPS += \
./Src/JPEGDecoder.d \
./Src/camera.d \
./Src/camera_i2c.d \
./Src/camera_spi.d \
./Src/lcd.d \
./Src/main.d 


# Each subdirectory must supply rules for building sources it contributes
Src/%.o Src/%.su Src/%.cyclo: ../Src/%.cpp Src/subdir.mk
	arm-none-eabi-g++ "$<" -mcpu=cortex-m7 -std=c++11 -g -DSTM32F746xx -c -I"/Users/ccoleman/Developer/harvard/tinyml/tiny_training/Src/TinyEngine/include" -I"/Users/ccoleman/Developer/harvard/tinyml/tiny_training/Src/TinyEngine/include/arm_cmsis" -I../Src -I../Inc -I../Drivers/STM32F7xx_HAL_Driver/Inc -I../Drivers/CMSIS/Device/ST/STM32F7xx/Include -I../Drivers/CMSIS/Include -I../Drivers/BSP/STM32746G-Discovery -I"/Users/ccoleman/Developer/harvard/tinyml/tiny_training/Src/TinyEngine/codegen/Include" -I"/Users/ccoleman/Developer/harvard/tinyml/tiny_training/Src/TinyEngine/include" -Ofast -ffunction-sections -fdata-sections -fno-exceptions -fno-rtti -fno-use-cxa-atexit -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@"  -mfpu=fpv5-sp-d16 -mfloat-abi=hard -mthumb -o "$@"
Src/%.o Src/%.su Src/%.cyclo: ../Src/%.c Src/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m7 -std=c11 -g -DSTM32F746xx -c -I../Src -I"/Users/ccoleman/Developer/harvard/tinyml/tiny_training/Src/TinyEngine/include" -I"/Users/ccoleman/Developer/harvard/tinyml/tiny_training/Src/TinyEngine/include/arm_cmsis" -I"/Users/ccoleman/Developer/harvard/tinyml/tiny_training/Src/TinyEngine/codegen/Include" -I../Inc -I../Drivers/STM32F7xx_HAL_Driver/Inc -I../Drivers/BSP/STM32746G-Discovery -I../Drivers/CMSIS/Include -I../Drivers/CMSIS/Device/ST/STM32F7xx/Include -I../TinyEngine/include -Ofast -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@"  -mfpu=fpv5-sp-d16 -mfloat-abi=hard -mthumb -o "$@"
Src/%.o: ../Src/%.s Src/subdir.mk
	arm-none-eabi-gcc -mcpu=cortex-m7 -g3 -DSTM32F746xx -c -IC:/Users/ASW-MNO-Admin/Atollic/TrueSTUDIO/ARM_videos/STM32F746G-Discovery/src -IC:/Users/ASW-MNO-Admin/Atollic/TrueSTUDIO/ARM_videos/STM32F746G-Discovery/Drivers/CMSIS/Include -IC:/Users/ASW-MNO-Admin/Atollic/TrueSTUDIO/ARM_videos/STM32F746G-Discovery/Drivers/CMSIS/Device/ST/STM32F7xx/Include -IC:/Users/ASW-MNO-Admin/Atollic/TrueSTUDIO/ARM_videos/STM32F746G-Discovery/Drivers/STM32F7xx_HAL_Driver/Inc -x assembler-with-cpp -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@"  -mfpu=fpv5-sp-d16 -mfloat-abi=hard -mthumb -o "$@" "$<"

clean: clean-Src

clean-Src:
	-$(RM) ./Src/JPEGDecoder.cyclo ./Src/JPEGDecoder.d ./Src/JPEGDecoder.o ./Src/JPEGDecoder.su ./Src/camera.cyclo ./Src/camera.d ./Src/camera.o ./Src/camera.su ./Src/camera_i2c.cyclo ./Src/camera_i2c.d ./Src/camera_i2c.o ./Src/camera_i2c.su ./Src/camera_spi.cyclo ./Src/camera_spi.d ./Src/camera_spi.o ./Src/camera_spi.su ./Src/lcd.cyclo ./Src/lcd.d ./Src/lcd.o ./Src/lcd.su ./Src/main.cyclo ./Src/main.d ./Src/main.o ./Src/main.su ./Src/picojpeg.cyclo ./Src/picojpeg.d ./Src/picojpeg.o ./Src/picojpeg.su ./Src/startup_stm32f746xx.d ./Src/startup_stm32f746xx.o ./Src/stm32f7xx_hal_msp.cyclo ./Src/stm32f7xx_hal_msp.d ./Src/stm32f7xx_hal_msp.o ./Src/stm32f7xx_hal_msp.su ./Src/stm32f7xx_it.cyclo ./Src/stm32f7xx_it.d ./Src/stm32f7xx_it.o ./Src/stm32f7xx_it.su ./Src/system_stm32f7xx.cyclo ./Src/system_stm32f7xx.d ./Src/system_stm32f7xx.o ./Src/system_stm32f7xx.su

.PHONY: clean-Src

