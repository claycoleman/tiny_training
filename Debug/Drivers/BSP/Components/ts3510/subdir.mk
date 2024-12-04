################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (12.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Drivers/BSP/Components/ts3510/ts3510.c 

C_DEPS += \
./Drivers/BSP/Components/ts3510/ts3510.d 

OBJS += \
./Drivers/BSP/Components/ts3510/ts3510.o 


# Each subdirectory must supply rules for building sources it contributes
Drivers/BSP/Components/ts3510/%.o Drivers/BSP/Components/ts3510/%.su Drivers/BSP/Components/ts3510/%.cyclo: ../Drivers/BSP/Components/ts3510/%.c Drivers/BSP/Components/ts3510/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m7 -std=c11 -g -DSTM32F746xx -c -I../Src -I"/Users/ccoleman/Developer/harvard/tinyml/tiny_training/Src/TinyEngine/include" -I"/Users/ccoleman/Developer/harvard/tinyml/tiny_training/Src/TinyEngine/include/arm_cmsis" -I"/Users/ccoleman/Developer/harvard/tinyml/tiny_training/Src/TinyEngine/codegen/Include" -I../Inc -I../Drivers/STM32F7xx_HAL_Driver/Inc -I../Drivers/BSP/STM32746G-Discovery -I../Drivers/CMSIS/Include -I../Drivers/CMSIS/Device/ST/STM32F7xx/Include -I../TinyEngine/include -Ofast -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@"  -mfpu=fpv5-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Drivers-2f-BSP-2f-Components-2f-ts3510

clean-Drivers-2f-BSP-2f-Components-2f-ts3510:
	-$(RM) ./Drivers/BSP/Components/ts3510/ts3510.cyclo ./Drivers/BSP/Components/ts3510/ts3510.d ./Drivers/BSP/Components/ts3510/ts3510.o ./Drivers/BSP/Components/ts3510/ts3510.su

.PHONY: clean-Drivers-2f-BSP-2f-Components-2f-ts3510

